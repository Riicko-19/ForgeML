"""Shared database setup for the HTTP integration tests."""

from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config

DEFAULT_URL = "postgresql+psycopg://forgeml:forgeml@127.0.0.1:55432/forgeml"
TABLES = ("audit_events", "package_validations", "operations", "packages")


def database_url() -> str:
    return os.environ.get("FORGEML_TEST_DATABASE_URL", DEFAULT_URL)


@pytest.fixture(scope="session")
def migrated() -> None:
    """Bring the schema to head once, via the migration the operator would run."""

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url())
    command.upgrade(config, "head")
