"""A real PostgreSQL 16 for the database gates.

ADR-009 rules SQLite out: durable operation claims depend on row-locking
semantics SQLite cannot express, so testing against it would prove nothing about
the code that ships.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from forgeml.infrastructure.database.engine import create_session_factory

DEFAULT_URL = "postgresql+psycopg://forgeml:forgeml@127.0.0.1:55432/forgeml"
TABLES = (
    "audit_events",
    "package_validations",
    "operations",
    "deployment_versions",
    "deployments",
    "packages",
)


def database_url() -> str:
    return os.environ.get("FORGEML_TEST_DATABASE_URL", DEFAULT_URL)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    engine = create_engine(database_url(), future=True)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url())
    # The schema under test is the one the migration builds -- never
    # metadata.create_all(), which would silently pass even if the migration
    # were broken.
    command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> Iterator[sessionmaker[Session]]:
    with engine.begin() as connection:
        connection.execute(
            text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
        )
    yield create_session_factory(engine)


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session
