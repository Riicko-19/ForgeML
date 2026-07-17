"""Migration gates (docs 06 phase 2 exit criteria)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine, create_engine, inspect, text

from forgeml.infrastructure.database.engine import create_session_factory
from forgeml.infrastructure.database.models import Base
from forgeml.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from tests.integration.database.conftest import database_url

EXPECTED_TABLES = {
    "packages",
    "package_validations",
    "operations",
    "audit_events",
    "deployments",
    "deployment_versions",
    "alembic_version",
}


@pytest.fixture
def alembic_config() -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url())
    return config


@pytest.fixture
def migrated_engine(engine: Engine, alembic_config: Config) -> Iterator[Engine]:
    yield engine
    # Whatever a test did to the schema, leave head behind for everyone else.
    command.upgrade(alembic_config, "head")


def test_the_models_match_the_migration(engine: Engine) -> None:
    """An empty autogenerate diff.

    This is the gate that catches a model changed without a migration -- the
    single most common way an ORM schema and a production database diverge.
    """

    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        difference = compare_metadata(context, Base.metadata)

    assert difference == []


def test_upgrade_downgrade_upgrade_is_clean(
    migrated_engine: Engine, alembic_config: Config
) -> None:
    command.downgrade(alembic_config, "base")

    remaining = set(inspect(migrated_engine).get_table_names())
    assert not (remaining & {"packages", "operations", "audit_events"})

    command.upgrade(alembic_config, "head")

    tables = set(inspect(migrated_engine).get_table_names())
    assert tables >= EXPECTED_TABLES


def test_downgrade_removes_the_triggers_it_created(
    migrated_engine: Engine, alembic_config: Config
) -> None:
    # A downgrade that leaves functions behind makes the next upgrade fail with
    # "function already exists" -- on a production rollback, at the worst moment.
    command.downgrade(alembic_config, "base")

    with migrated_engine.connect() as connection:
        functions = connection.execute(
            text("SELECT count(*) FROM pg_proc WHERE proname LIKE 'forgeml_%'")
        ).scalar_one()

    assert functions == 0

    command.upgrade(alembic_config, "head")


def test_offline_sql_generation_works(alembic_config: Config) -> None:
    """Docs 11 requires an operator to be able to review DDL before applying it."""

    command.upgrade(alembic_config, "head", sql=True)


def test_a_closed_unit_of_work_cannot_be_committed(engine: Engine) -> None:
    # Committing outside the context would commit into a session that no longer
    # exists; failing loudly beats silently doing nothing.
    uow = SqlAlchemyUnitOfWork(create_session_factory(engine))

    with pytest.raises(RuntimeError, match="not open"):
        uow.commit()


def test_a_fresh_database_reaches_head(alembic_config: Config) -> None:
    url = database_url()
    engine = create_engine(url, future=True)
    try:
        with engine.connect() as connection:
            version = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
        assert version
    finally:
        engine.dispose()
