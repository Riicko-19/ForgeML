"""Schema for the identity integration tests.

Brought to head through the migration an operator would run, not through
`metadata.create_all()` -- a schema built the second way would pass even if the
migration that ships were broken.
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config

from tests.integration.api.conftest import database_url

#: Resolved at conftest import, before any fixture can touch the environment.
#:
#: `database_url()` reads `FORGEML_TEST_DATABASE_URL` and falls back to a
#: localhost default. The CLI tests *delete* that variable, because
#: configuration is fail-closed on unknown `FORGEML_*` names -- so any later
#: call to `database_url()` silently returns the fallback rather than the
#: database the harness was pointed at. On a machine where the fallback happens
#: to be right that reads as working; on CI it reads as connection refused.
#:
#: Everything in this package uses this constant, never `database_url()`.
TEST_DATABASE_URL = database_url()


@pytest.fixture(scope="session")
def migrated() -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(config, "head")
