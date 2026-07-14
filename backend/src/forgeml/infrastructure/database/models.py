"""SQLAlchemy mappings. The only ORM classes in ForgeML.

Nothing here leaves this package. Repositories map these rows to immutable
domain records, so no lazy load can fire outside a session and no ORM identity
reaches domain policy.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Deterministic constraint names, so an Alembic autogenerate diff is meaningful
# and a migration can drop a constraint it did not explicitly name.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

PACKAGE_STATES = ("draft", "validating", "validated", "rejected")
VALIDATION_STATES = ("validated", "rejected")
OPERATION_STATES = ("pending", "running", "succeeded", "failed")
ACTOR_TYPES = ("operator", "system")


def _in_check(column: str, values: tuple[str, ...]) -> str:
    allowed = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({allowed})"


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class PackageRow(Base):
    __tablename__ = "packages"
    __table_args__ = (
        CheckConstraint(_in_check("state", PACKAGE_STATES), name="state"),
        CheckConstraint("size_bytes > 0", name="size_positive"),
        CheckConstraint(
            "manifest_version IS NULL OR manifest_version > 0",
            name="manifest_version_positive",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    # ADR-003: the checksum is the identity. This unique index is what makes a
    # duplicate upload idempotent -- not an application-level existence check,
    # which two concurrent uploads would both pass.
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    filename: Mapped[str] = mapped_column(String(512))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    # Null until validated: the bytes are stored before anything parses them.
    manifest_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str] = mapped_column(String(16))
    artifact_uri: Mapped[str] = mapped_column(Text)
    manifest: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PackageValidationRow(Base):
    __tablename__ = "package_validations"
    __table_args__ = (
        # Revalidating with the same validator is idempotent; a new validator
        # version produces a new row and retains the earlier verdict.
        UniqueConstraint("package_id", "validator_version"),
        CheckConstraint(_in_check("state", VALIDATION_STATES), name="state"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    package_id: Mapped[UUID] = mapped_column(
        ForeignKey("packages.id", ondelete="CASCADE"), index=True
    )
    validator_version: Mapped[str] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(16))
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    manifest: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OperationRow(Base):
    __tablename__ = "operations"
    __table_args__ = (
        # The whole idempotency contract of docs 04, in one constraint.
        UniqueConstraint("idempotency_key", "type", "target_id"),
        CheckConstraint(_in_check("state", OPERATION_STATES), name="state"),
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        # The claim query reads only pending rows; a partial index keeps it from
        # walking terminal history that grows without bound.
        Index(
            "ix_operations_claimable",
            "created_at",
            postgresql_where=text("state = 'pending'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[str] = mapped_column(String(255), index=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16))
    correlation_id: Mapped[UUID] = mapped_column()
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    failure: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint(_in_check("actor_type", ACTOR_TYPES), name="actor_type"),
        Index("ix_audit_events_target", "target_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(16))
    action: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str] = mapped_column(String(128))
    target_id: Mapped[str] = mapped_column(String(128))
    correlation_id: Mapped[UUID] = mapped_column(index=True)
    event_metadata: Mapped[dict[str, str]] = mapped_column(
        "metadata", JSONB, default=dict
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
