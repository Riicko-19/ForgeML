"""module 2 metadata layer

Revision ID: 0d7adf1f94cf
Revises:
Create Date: 2026-07-14 22:34:30.803815

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0d7adf1f94cf"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# These invariants are enforced by the database, not only by the repositories.
# ADR-003 makes a package checksum and its artifact immutable, and docs 04 makes
# terminal operations and audit events immutable. Repository discipline protects
# them from our code; a trigger protects them from an operator with psql open,
# which is precisely the actor ADR-004 warns about.
IMMUTABILITY_DDL = (
    """
    CREATE FUNCTION forgeml_packages_immutable() RETURNS trigger AS $$
    BEGIN
        IF NEW.sha256 IS DISTINCT FROM OLD.sha256
           OR NEW.artifact_uri IS DISTINCT FROM OLD.artifact_uri THEN
            RAISE EXCEPTION
                'package checksum and artifact are immutable (ADR-003)';
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """,
    """
    CREATE TRIGGER packages_immutable BEFORE UPDATE ON packages
    FOR EACH ROW EXECUTE FUNCTION forgeml_packages_immutable();
    """,
    """
    CREATE FUNCTION forgeml_operations_terminal() RETURNS trigger AS $$
    BEGIN
        IF OLD.state IN ('succeeded', 'failed') THEN
            RAISE EXCEPTION 'a terminal operation is immutable (docs 04)';
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """,
    """
    CREATE TRIGGER operations_terminal BEFORE UPDATE ON operations
    FOR EACH ROW EXECUTE FUNCTION forgeml_operations_terminal();
    """,
    """
    CREATE FUNCTION forgeml_audit_append_only() RETURNS trigger AS $$
    BEGIN
        RAISE EXCEPTION 'audit events are append-only (docs 04)';
    END;
    $$ LANGUAGE plpgsql;
    """,
    """
    CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION forgeml_audit_append_only();
    """,
)

DROP_IMMUTABILITY_DDL = (
    "DROP TRIGGER IF EXISTS audit_append_only ON audit_events;",
    "DROP FUNCTION IF EXISTS forgeml_audit_append_only();",
    "DROP TRIGGER IF EXISTS operations_terminal ON operations;",
    "DROP FUNCTION IF EXISTS forgeml_operations_terminal();",
    "DROP TRIGGER IF EXISTS packages_immutable ON packages;",
    "DROP FUNCTION IF EXISTS forgeml_packages_immutable();",
)


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_type", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=128), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "actor_type IN ('operator', 'system')",
            name=op.f("ck_audit_events_actor_type"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(
        op.f("ix_audit_events_correlation_id"),
        "audit_events",
        ["correlation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_events_occurred_at"),
        "audit_events",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_target",
        "audit_events",
        ["target_id", "occurred_at"],
        unique=False,
    )
    op.create_table(
        "operations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("failure", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "state IN ('pending', 'running', 'succeeded', 'failed')",
            name=op.f("ck_operations_state"),
        ),
        sa.CheckConstraint(
            "attempts >= 0", name=op.f("ck_operations_attempts_non_negative")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_operations")),
        sa.UniqueConstraint(
            "idempotency_key",
            "type",
            "target_id",
            name=op.f("uq_operations_idempotency_key_type_target_id"),
        ),
    )
    op.create_index(
        "ix_operations_claimable",
        "operations",
        ["created_at"],
        unique=False,
        postgresql_where=sa.text("state = 'pending'"),
    )
    op.create_index(
        op.f("ix_operations_target_id"), "operations", ["target_id"], unique=False
    )
    op.create_table(
        "packages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("manifest_version", sa.Integer(), nullable=True),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("artifact_uri", sa.Text(), nullable=False),
        sa.Column("manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('draft', 'validating', 'validated', 'rejected')",
            name=op.f("ck_packages_state"),
        ),
        sa.CheckConstraint(
            "manifest_version IS NULL OR manifest_version > 0",
            name=op.f("ck_packages_manifest_version_positive"),
        ),
        sa.CheckConstraint("size_bytes > 0", name=op.f("ck_packages_size_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_packages")),
        sa.UniqueConstraint("sha256", name=op.f("uq_packages_sha256")),
    )
    op.create_table(
        "package_validations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("package_id", sa.Uuid(), nullable=False),
        sa.Column("validator_version", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("findings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('validated', 'rejected')",
            name=op.f("ck_package_validations_state"),
        ),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["packages.id"],
            name=op.f("fk_package_validations_package_id_packages"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_package_validations")),
        sa.UniqueConstraint(
            "package_id",
            "validator_version",
            name=op.f("uq_package_validations_package_id_validator_version"),
        ),
    )
    op.create_index(
        op.f("ix_package_validations_package_id"),
        "package_validations",
        ["package_id"],
        unique=False,
    )

    for statement in IMMUTABILITY_DDL:
        op.execute(statement)


def downgrade() -> None:
    for statement in DROP_IMMUTABILITY_DDL:
        op.execute(statement)

    op.drop_index(
        op.f("ix_package_validations_package_id"), table_name="package_validations"
    )
    op.drop_table("package_validations")
    op.drop_table("packages")
    op.drop_index(op.f("ix_operations_target_id"), table_name="operations")
    op.drop_index(
        "ix_operations_claimable",
        table_name="operations",
        postgresql_where=sa.text("state = 'pending'"),
    )
    op.drop_table("operations")
    op.drop_index("ix_audit_events_target", table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_occurred_at"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_correlation_id"), table_name="audit_events")
    op.drop_table("audit_events")
    # ### end Alembic commands ###
