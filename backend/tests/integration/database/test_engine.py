"""The engine the control plane actually builds, against a real database.

Every other test constructs an engine directly. That leaves the production
factory -- pool settings, driver, and the statement timeout that stops a
pathological query pinning a connection -- entirely unexercised.
"""

from __future__ import annotations

from importlib import metadata

import pytest
from sqlalchemy import text

from forgeml.core.config import Environment, load_settings
from forgeml.infrastructure.database.engine import create_database_engine
from tests.integration.database.conftest import database_url


@pytest.fixture(autouse=True)
def installed_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")


def settings(**overrides: str) -> object:
    values = {
        "FORGEML_ENVIRONMENT": "test",
        "FORGEML_DATABASE_URL": database_url(),
    }
    values.update(overrides)
    return load_settings(values)


def test_the_configured_engine_connects_and_applies_its_statement_timeout() -> None:
    configured = load_settings(
        {
            "FORGEML_ENVIRONMENT": "test",
            "FORGEML_DATABASE_URL": database_url(),
            "FORGEML_DATABASE_STATEMENT_TIMEOUT_MS": "7000",
        }
    )

    engine = create_database_engine(configured)
    try:
        with engine.connect() as connection:
            timeout = connection.execute(text("SHOW statement_timeout")).scalar_one()
    finally:
        engine.dispose()

    assert timeout == "7s"


def test_the_database_url_is_never_disclosed() -> None:
    configured = load_settings(
        {"FORGEML_ENVIRONMENT": "test", "FORGEML_DATABASE_URL": database_url()}
    )

    # The URL carries the database password. It must not leak through a repr, a
    # log record, or an error rendered from settings.
    assert "forgeml:forgeml" not in repr(configured)
    assert "forgeml:forgeml" not in str(configured.database_url)
    assert configured.environment is Environment.TEST
    assert configured.require_database_url() == database_url()


def test_a_non_postgresql_url_fails_closed() -> None:
    # ADR-009: SQLite cannot express the row-locking semantics durable operation
    # claims rely on, so it must fail at configuration rather than at 3am.
    from forgeml.core.config import ConfigurationFailure

    with pytest.raises(ConfigurationFailure):
        load_settings(
            {
                "FORGEML_ENVIRONMENT": "test",
                "FORGEML_DATABASE_URL": "sqlite:///forgeml.db",
            }
        )
