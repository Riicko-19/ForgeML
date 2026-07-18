"""Credential verification against a store (ADR-024, ADR-025).

Drives the real `ApiKeyVerifier` over the in-memory store, which is held to the
same conformance suite as the PostgreSQL one.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from forgeml.application.identity.services import ApiKeyAdministration, ApiKeyVerifier
from forgeml.domain.identity import credentials
from forgeml.domain.identity.models import ActorType, AuthenticationMethod
from tests.fakes import InMemoryUnitOfWork

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


@pytest.fixture
def uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


def _admin(uow: InMemoryUnitOfWork, now: datetime = NOW) -> ApiKeyAdministration:
    return ApiKeyAdministration(lambda: uow, clock=lambda: now)


def _verifier(uow: InMemoryUnitOfWork, now: datetime = NOW) -> ApiKeyVerifier:
    return ApiKeyVerifier(lambda: uow, clock=lambda: now)


def test_a_valid_key_authenticates_as_an_operator(uow: InMemoryUnitOfWork) -> None:
    token = _admin(uow).create(name="ci")

    context = _verifier(uow).verify(token)

    assert context is not None
    assert context.principal.actor_type is ActorType.OPERATOR
    assert context.principal.actor_id == token.split("_")[1]
    assert context.method is AuthenticationMethod.API_KEY


@pytest.mark.parametrize(
    "presented",
    [
        "",
        "garbage",
        "forge_" + "0" * 16 + "_nonexistent",
        "Bearer forge_x_y",
    ],
)
def test_an_unusable_credential_authenticates_nothing(
    uow: InMemoryUnitOfWork, presented: str
) -> None:
    _admin(uow).create(name="ci")

    assert _verifier(uow).verify(presented) is None


def test_the_right_key_id_with_the_wrong_secret_is_refused(
    uow: InMemoryUnitOfWork,
) -> None:
    token = _admin(uow).create(name="ci")
    key_id = token.split("_")[1]

    assert _verifier(uow).verify(f"forge_{key_id}_wrong-secret") is None


def test_a_revoked_key_stops_working_immediately(uow: InMemoryUnitOfWork) -> None:
    """No cache, no grace period: revocation takes effect on the next request."""

    token = _admin(uow).create(name="ci")
    assert _verifier(uow).verify(token) is not None

    _admin(uow).revoke(token.split("_")[1])

    assert _verifier(uow).verify(token) is None


def test_an_expired_key_is_refused(uow: InMemoryUnitOfWork) -> None:
    token = _admin(uow).create(name="ci", expires_in_days=1)

    assert _verifier(uow, NOW).verify(token) is not None
    assert _verifier(uow, NOW + timedelta(days=2)).verify(token) is None


def test_every_failure_is_indistinguishable_to_the_caller(
    uow: InMemoryUnitOfWork,
) -> None:
    """ADR-025: one outcome for every rejection.

    Unknown, wrong, revoked, and expired must be the same `None`. Any richer
    return would eventually become a richer HTTP response, and that is an
    enumeration oracle.
    """

    live = _admin(uow).create(name="live")
    revoked = _admin(uow).create(name="revoked")
    expired = _admin(uow).create(name="expired", expires_in_days=1)
    _admin(uow).revoke(revoked.split("_")[1])
    later = NOW + timedelta(days=2)

    outcomes = {
        "unknown": _verifier(uow, later).verify("forge_" + "0" * 16 + "_x"),
        "wrong_secret": _verifier(uow, later).verify(
            f"forge_{live.split('_')[1]}_wrong"
        ),
        "revoked": _verifier(uow, later).verify(revoked),
        "expired": _verifier(uow, later).verify(expired),
        "malformed": _verifier(uow, later).verify("nonsense"),
    }

    assert set(outcomes.values()) == {None}


def test_the_presented_secret_never_reaches_the_log(
    uow: InMemoryUnitOfWork, caplog: pytest.LogCaptureFixture
) -> None:
    """ADR-025: only key_id is loggable, and it is not secret by construction."""

    token = _admin(uow).create(name="ci")
    key_id, secret = token.split("_")[1], token.split("_", 2)[2]

    with caplog.at_level("DEBUG"):
        _verifier(uow).verify(f"forge_{key_id}_wrong-secret-here")
        _verifier(uow).verify(token)
        _verifier(uow).verify("forge_" + "0" * 16 + "_" + secret)

    # Structured fields as well as the rendered message: the production logger
    # serializes `extra`, so a secret smuggled in there would reach the log file
    # even though it never appears in caplog.text.
    emitted = caplog.text + "".join(
        f"{key}={value}"
        for record in caplog.records
        for key, value in record.__dict__.items()
    )

    assert secret not in emitted
    assert "wrong-secret-here" not in emitted
    # The operator still gets something to act on.
    assert any(getattr(record, "key_id", None) == key_id for record in caplog.records)


def test_use_is_recorded_for_compromise_review(uow: InMemoryUnitOfWork) -> None:
    token = _admin(uow).create(name="ci")
    used_at = NOW + timedelta(hours=3)

    _verifier(uow, used_at).verify(token)

    with uow:
        (stored,) = uow.api_keys.list()
    assert stored.last_used_at == used_at


def test_authentication_survives_a_failure_to_record_use(
    uow: InMemoryUnitOfWork,
) -> None:
    """Bookkeeping must not be able to reject a valid credential."""

    token = _admin(uow).create(name="ci")
    verifier = _verifier(uow)

    def explode(*_: object, **__: object) -> None:
        raise RuntimeError("database hiccup")

    with uow:
        uow.api_keys.touch_last_used = explode  # type: ignore[method-assign]

    assert verifier.verify(token) is not None


def test_creating_a_key_stores_only_a_digest(uow: InMemoryUnitOfWork) -> None:
    token = _admin(uow).create(name="ci")
    secret = token.split("_", 2)[2]

    with uow:
        (stored,) = uow.api_keys.list()

    assert stored.secret_sha256 == credentials.hash_secret(secret)
    assert secret not in stored.secret_sha256


def test_revoking_an_unknown_key_is_an_error(uow: InMemoryUnitOfWork) -> None:
    from forgeml.core.errors import AppError

    with pytest.raises(AppError, match="api key"):
        _admin(uow).revoke("0" * 16)


def test_revocation_keeps_the_first_timestamp(uow: InMemoryUnitOfWork) -> None:
    """The first revocation is the one the incident timeline needs."""

    token = _admin(uow).create(name="ci")
    key_id = token.split("_")[1]

    _admin(uow, NOW).revoke(key_id)
    _admin(uow, NOW + timedelta(days=1)).revoke(key_id)

    with uow:
        (stored,) = uow.api_keys.list()
    assert stored.revoked_at == NOW
