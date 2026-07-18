"""epic 1 identity and authentication

Adds the `api_keys` table (ADR-024) and `audit_events.actor_id` (ADR-018).

Additive and reversible. `actor_id` is nullable **with no backfill**: historical
rows genuinely had no recorded principal, and writing a synthetic value would
forge the audit trail the column exists to protect. Rollback drops both, and no
code path requires either to be present.

`audit_events` carries an immutability trigger from Module 2. Adding a column
does not disturb it -- the new column is append-only like every other, because
the trigger forbids UPDATE on the whole row.

Revision ID: 3c7d8e9f0a1b
Revises: 2f6b4b3d36ac
Create Date: 2026-07-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3c7d8e9f0a1b"
down_revision: str | None = "2f6b4b3d36ac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        # The SHA-256 digest of the secret, hex encoded. The secret itself is
        # never stored, so this table cannot yield a working credential.
        sa.Column("secret_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_keys")),
        sa.UniqueConstraint("key_id", name=op.f("uq_api_keys_key_id")),
    )

    op.add_column(
        "audit_events",
        sa.Column("actor_id", sa.String(length=64), nullable=True),
    )
    # "Everything this principal did" is where an audit review begins, so the
    # column is indexed from the moment it exists rather than after the first
    # slow query during an incident.
    op.create_index(
        op.f("ix_audit_events_actor_id"), "audit_events", ["actor_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_events_actor_id"), table_name="audit_events")
    op.drop_column("audit_events", "actor_id")
    op.drop_table("api_keys")
