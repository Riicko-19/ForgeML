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
DESIRED_STATES = ("running", "stopped")
VERSION_STATES = ("building", "starting", "ready", "active", "failed", "stopped")


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
    # Null unless the package validated: the Module 4 analyzed inference
    # contract (docs 04). Added additively; a rejected row leaves it null.
    contract: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
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


class DeploymentRow(Base):
    __tablename__ = "deployments"
    __table_args__ = (
        CheckConstraint(_in_check("desired_state", DESIRED_STATES), name="desired"),
        UniqueConstraint("name"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    # DNS-label shaped and immutable after creation (docs 12).
    name: Mapped[str] = mapped_column(String(63))
    desired_state: Mapped[str] = mapped_column(String(16))
    # Nullable; the routing module (Module 7) owns setting the active version, so
    # no database foreign key is declared here yet -- it would be a forward
    # reference to a row a later module activates.
    active_version_id: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DeploymentVersionRow(Base):
    __tablename__ = "deployment_versions"
    __table_args__ = (
        CheckConstraint(_in_check("state", VERSION_STATES), name="state"),
        CheckConstraint("attempt > 0", name="attempt_positive"),
        # Attempt is monotonic per deployment and package: a retry of the same
        # package is a new attempt, and no two attempts share a number.
        UniqueConstraint("deployment_id", "package_id", "attempt"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    deployment_id: Mapped[UUID] = mapped_column(
        ForeignKey("deployments.id", ondelete="CASCADE"), index=True
    )
    package_id: Mapped[UUID] = mapped_column(ForeignKey("packages.id"))
    attempt: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(16))
    resource_policy: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    image_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    container_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    endpoint: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint(_in_check("actor_type", ACTOR_TYPES), name="actor_type"),
        Index("ix_audit_events_target", "target_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(16))
    # Nullable by ADR-018: SYSTEM actions have no principal, and rows written
    # before Epic 1 genuinely had none. Indexed for "everything this principal
    # did", which is where every audit review starts.
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
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


class ApiKeyRow(Base):
    """A stored API key (ADR-024). Holds a digest, never a secret."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    key_id: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    secret_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
