"""Identity values (ADR-023)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from forgeml.domain.identity.models import ActorType, ApiKey, Principal

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def _key(**overrides: object) -> ApiKey:
    fields: dict[str, object] = {
        "id": uuid4(),
        "key_id": "a" * 16,
        "name": "ci",
        "secret_sha256": "b" * 64,
        "created_at": NOW,
    }
    fields.update(overrides)
    return ApiKey(**fields)  # type: ignore[arg-type]


def test_a_principal_carries_identity_and_nothing_else() -> None:
    """A Principal is *who*, never *how they proved it* (ADR-023).

    Asserted structurally: if a credential field ever appears here it will end
    up in an audit row and a log line, which is exactly what the split exists
    to prevent.
    """

    principal = Principal(actor_type=ActorType.OPERATOR, actor_id="abc")

    assert set(Principal.__slots__) == {"actor_type", "actor_id"}
    assert principal.actor_id == "abc"


@pytest.mark.parametrize("actor_id", ["", "x" * 65, "with\nnewline", "null\x00byte"])
def test_an_unsafe_actor_id_is_refused(actor_id: str) -> None:
    """Identity reaches logs and audit rows, so it is bounded like they are."""

    with pytest.raises(ValueError):
        Principal(actor_type=ActorType.OPERATOR, actor_id=actor_id)


def test_a_fresh_key_is_usable() -> None:
    assert _key().is_usable(NOW)


def test_a_revoked_key_is_not_usable() -> None:
    assert not _key(revoked_at=NOW).is_usable(NOW + timedelta(seconds=1))


def test_an_expired_key_is_not_usable() -> None:
    assert not _key(expires_at=NOW).is_usable(NOW + timedelta(seconds=1))


def test_a_key_expiring_later_is_still_usable() -> None:
    assert _key(expires_at=NOW + timedelta(days=1)).is_usable(NOW)


def test_expiry_is_exclusive_at_the_boundary() -> None:
    """`expires_at == now` is expired. A key is not usable *at* its expiry."""

    assert not _key(expires_at=NOW).is_usable(NOW)


def test_a_revoked_and_expired_key_is_not_usable() -> None:
    assert not _key(revoked_at=NOW, expires_at=NOW).is_usable(NOW)


def test_a_key_authenticates_as_an_operator_identified_by_its_public_handle() -> None:
    """actor_id is the key_id, which is not secret by construction (ADR-024)."""

    key = _key(key_id="c" * 16)

    principal = key.principal()

    assert principal.actor_type is ActorType.OPERATOR
    assert principal.actor_id == "c" * 16
    assert key.secret_sha256 not in principal.actor_id
