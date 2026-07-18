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


@pytest.fixture(scope="session")
def migrated() -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url())
    command.upgrade(config, "head")
