"""module 4 analyzed contract

Adds the nullable `contract` column to `package_validations` -- the analyzed
inference contract (docs 04) that Module 2 deliberately deferred to Module 4
(see docs 34). Additive and reversible: existing rows keep null, and no existing
behaviour changes when the contract is absent.

Revision ID: 1a2b3c4d5e6f
Revises: 0d7adf1f94cf
Create Date: 2026-07-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "1a2b3c4d5e6f"
down_revision: str | None = "0d7adf1f94cf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "package_validations",
        sa.Column("contract", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("package_validations", "contract")
