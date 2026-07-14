"""Alembic environment.

The database URL comes from the same typed, fail-closed configuration the
application uses. Alembic never reads its own connection string from a file, so
there is no second place for a credential to live.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from forgeml.core.config import load_settings
from forgeml.infrastructure.database.models import Base

config = context.config
target_metadata = Base.metadata


def _database_url() -> str:
    """The URL supplied by the caller, else the application's own configuration.

    Tests and tooling pass an explicit URL on the Alembic config; the CLI passes
    nothing and inherits the same fail-closed settings the control plane uses.
    """

    configured = config.get_main_option("sqlalchemy.url", "")
    return configured or load_settings().require_database_url()


def run_migrations_offline() -> None:
    """Emit SQL without a connection, so an operator can review DDL first."""

    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database."""

    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
