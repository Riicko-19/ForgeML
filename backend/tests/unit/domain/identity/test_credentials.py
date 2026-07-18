"""Token policy (ADR-024). Pure functions, so these can be exhaustive."""

from __future__ import annotations

import hashlib

import pytest

from forgeml.domain.identity import credentials


def test_a_generated_token_parses_back_to_its_parts() -> None:
    generated = credentials.generate()

    parsed = credentials.parse(generated.token)

    assert parsed is not None
    assert parsed.key_id == generated.key_id
    assert credentials.matches(parsed.secret, generated.secret_sha256)


def test_the_secret_is_never_recoverable_from_what_is_stored() -> None:
    """The property that matters when the database is what leaks."""

    generated = credentials.generate()

    parsed = credentials.parse(generated.token)

    assert parsed is not None
    assert parsed.secret not in generated.secret_sha256
    assert (
        generated.secret_sha256
        == hashlib.sha256(parsed.secret.encode("utf-8")).hexdigest()
    )


def test_every_generated_key_is_unique() -> None:
    tokens = {credentials.generate().token for _ in range(200)}
    key_ids = {credentials.generate().key_id for _ in range(200)}

    assert len(tokens) == 200
    assert len(key_ids) == 200


def test_the_secret_carries_the_entropy_the_hashing_decision_rests_on() -> None:
    """ADR-024 chose SHA-256 over a KDF *because* of this width.

    If the secret ever shrinks, that decision has to be revisited, so the number
    is asserted rather than trusted -- a silent narrowing here would quietly
    invalidate the reasoning without failing anything else.
    """

    assert credentials.SECRET_BYTES == 32

    parsed = credentials.parse(credentials.generate().token)

    assert parsed is not None
    # 32 bytes base64url-encoded, unpadded.
    assert len(parsed.secret) == 43


@pytest.mark.parametrize(
    "token",
    [
        "",
        "forge",
        "forge_",
        "forge_abc",
        "forge_abc_secret",  # key_id too short
        "forge_" + "a" * 16,  # no secret
        "forge_" + "a" * 16 + "_",  # empty secret
        "wrong_" + "a" * 16 + "_secret",  # wrong prefix
        "forge_" + "g" * 16 + "_secret",  # key_id is not hex
        "forge_" + "A" * 16 + "_secret",  # uppercase is not our alphabet
        "Bearer forge_" + "a" * 16 + "_secret",  # scheme left on
        "forge__secret",
        "notatokenatall",
    ],
)
def test_malformed_tokens_are_refused(token: str) -> None:
    assert credentials.parse(token) is None


def test_a_secret_containing_underscores_survives_parsing() -> None:
    """token_urlsafe emits `_`, so only the first two separators are structural.

    A naive split would truncate the secret and silently compare a prefix.
    """

    token = "forge_" + "a" * 16 + "_secret_with_many_underscores"

    parsed = credentials.parse(token)

    assert parsed is not None
    assert parsed.secret == "secret_with_many_underscores"


def test_a_wrong_secret_does_not_match() -> None:
    generated = credentials.generate()

    assert not credentials.matches("wrong", generated.secret_sha256)


def test_the_miss_path_is_callable_and_discards_its_result() -> None:
    """`absorb_miss` exists for its cost, not its result (ADR-024).

    It must never raise, whatever it is handed: it runs on the branch where an
    attacker controls the input and no key was found.
    """

    credentials.absorb_miss("anything")
    credentials.absorb_miss("")
    credentials.absorb_miss("\u0000\uffff")
