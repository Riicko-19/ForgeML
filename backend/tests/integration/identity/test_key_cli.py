"""The key administration CLI (ADR-026).

This is the only way to mint a credential, so it is on the critical path of
every first run. It is tested through `main()` with a real database, because
what an operator types is the contract.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text

from forgeml.domain.identity import credentials
from forgeml.identity.__main__ import main
from tests.integration.identity.conftest import TEST_DATABASE_URL


@pytest.fixture
def clean_keys(migrated: None) -> Iterator[None]:
    engine = create_engine(TEST_DATABASE_URL, future=True)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE api_keys RESTART IDENTITY CASCADE"))
    engine.dispose()
    yield


@pytest.fixture(autouse=True)
def database_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment an operator running the CLI would have.

    `FORGEML_TEST_DATABASE_URL` is removed on purpose. Configuration is
    fail-closed on any unknown `FORGEML_*` variable, and that one is a
    *test-harness* variable, not a setting -- leaving it set makes the CLI exit
    with a configuration error. That is correct behaviour and worth knowing
    about: a developer with it exported in their shell will see the same thing.

    The URL comes from the package constant, not from `database_url()`, for
    the reason recorded in this package's conftest.
    """

    monkeypatch.delenv("FORGEML_TEST_DATABASE_URL", raising=False)
    monkeypatch.setenv("FORGEML_ENVIRONMENT", "test")
    monkeypatch.setenv("FORGEML_DATABASE_URL", TEST_DATABASE_URL)


def test_create_prints_a_usable_token_exactly_once(
    clean_keys: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["create", "--name", "ci-pipeline"]) == 0

    printed = capsys.readouterr().out
    token = next(word for word in printed.split() if word.startswith("forge_"))
    parsed = credentials.parse(token)

    assert parsed is not None
    assert "ci-pipeline" in printed
    assert "only time" in printed


def test_a_created_key_authenticates(
    clean_keys: None, capsys: pytest.CaptureFixture[str]
) -> None:
    """The whole point: what the CLI prints is what the API accepts."""

    from forgeml.application.identity.services import ApiKeyVerifier
    from forgeml.core.config import load_settings
    from forgeml.infrastructure.database.provider import DatabaseProvider

    main(["create", "--name", "ci"])
    token = next(
        word for word in capsys.readouterr().out.split() if word.startswith("forge_")
    )

    provider = DatabaseProvider(load_settings())
    try:
        context = ApiKeyVerifier(provider.unit_of_work).verify(token)
    finally:
        provider.dispose()

    assert context is not None
    assert context.principal.actor_id == token.split("_")[1]


def test_the_secret_is_not_recoverable_from_the_database(
    clean_keys: None, capsys: pytest.CaptureFixture[str]
) -> None:
    """ADR-026: only a digest is stored, so a dump yields nothing usable."""

    main(["create", "--name", "ci"])
    token = next(
        word for word in capsys.readouterr().out.split() if word.startswith("forge_")
    )
    secret = token.split("_", 2)[2]

    engine = create_engine(TEST_DATABASE_URL, future=True)
    with engine.connect() as connection:
        stored = connection.execute(text("SELECT * FROM api_keys")).mappings().all()
    engine.dispose()

    assert secret not in str(stored)


def test_list_shows_keys_without_secrets(
    clean_keys: None, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["create", "--name", "alpha"])
    token = next(
        word for word in capsys.readouterr().out.split() if word.startswith("forge_")
    )

    assert main(["list"]) == 0

    printed = capsys.readouterr().out
    assert "alpha" in printed
    assert token.split("_", 2)[2] not in printed
    assert "never" in printed  # last used


def test_list_is_helpful_when_there_are_no_keys(
    clean_keys: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["list"]) == 0

    assert "No API keys" in capsys.readouterr().out


def test_revoke_stops_the_key_working(
    clean_keys: None, capsys: pytest.CaptureFixture[str]
) -> None:
    from forgeml.application.identity.services import ApiKeyVerifier
    from forgeml.core.config import load_settings
    from forgeml.infrastructure.database.provider import DatabaseProvider

    main(["create", "--name", "ci"])
    token = next(
        word for word in capsys.readouterr().out.split() if word.startswith("forge_")
    )
    key_id = token.split("_")[1]

    assert main(["revoke", key_id]) == 0

    provider = DatabaseProvider(load_settings())
    try:
        assert ApiKeyVerifier(provider.unit_of_work).verify(token) is None
    finally:
        provider.dispose()
    assert main(["list"]) == 0
    assert "revoked" in capsys.readouterr().out


def test_revoking_an_unknown_key_fails_without_a_traceback(
    clean_keys: None, capsys: pytest.CaptureFixture[str]
) -> None:
    """An operator's terminal is no place for a stack trace: it is noise, and it
    can carry a connection string."""

    assert main(["revoke", "0" * 16]) == 1

    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "Traceback" not in captured.err
    assert TEST_DATABASE_URL not in captured.err


def test_an_expiring_key_can_be_created(
    clean_keys: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["create", "--name", "temporary", "--expires-days", "7"]) == 0

    assert "temporary" in capsys.readouterr().out


def test_a_missing_database_configuration_exits_cleanly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("FORGEML_DATABASE_URL", raising=False)
    monkeypatch.delenv("FORGEML_ENVIRONMENT", raising=False)

    assert main(["list"]) == 2

    captured = capsys.readouterr()
    assert "configuration error" in captured.err
    assert "Traceback" not in captured.err


def test_a_command_is_required(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main([])
