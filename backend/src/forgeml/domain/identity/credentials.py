"""API-key token policy (ADR-024): generate, parse, hash, compare.

Pure functions over values. No I/O, no clock, no store -- which is what lets the
security-critical part of authentication be tested exhaustively without a
database.

**The token format is `forge_<key_id>_<secret>`.**

`key_id` is 16 hex characters and is *not* secret: it is the lookup handle and
the `actor_id`, and it appears in logs and audit rows by design. `secret` is 43
characters carrying 256 bits of CSPRNG entropy, is never stored, and is shown
exactly once. The `forge_` prefix exists so the credential is greppable in a
leaked file -- it is what makes secret-scanning tools able to find it.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

PREFIX = "forge"
KEY_ID_BYTES = 8
#: 256 bits from the OS CSPRNG. ADR-024's choice of a plain SHA-256 verifier
#: over a password KDF rests entirely on this number: there is no guess space to
#: protect, so a work factor would buy nothing and cost latency on every
#: request. If a change ever lets this secret be shorter, human-chosen, or
#: derived, that ADR must be revisited in the same commit.
SECRET_BYTES = 32

KEY_ID_LENGTH = KEY_ID_BYTES * 2

#: Compared against on the lookup-miss path so that an unknown key_id costs the
#: same as a wrong secret. Without it, latency distinguishes the two and an
#: attacker can enumerate valid key_ids.
_DUMMY_DIGEST = hashlib.sha256(b"forgeml-nonexistent-credential").hexdigest()


@dataclass(frozen=True, slots=True)
class PresentedKey:
    """A syntactically valid token, split into its lookup handle and its proof."""

    key_id: str
    secret: str


@dataclass(frozen=True, slots=True)
class GeneratedKey:
    """A freshly minted key: the token to show once, and the digest to store."""

    key_id: str
    token: str
    secret_sha256: str


def generate() -> GeneratedKey:
    """Mint a new API key.

    The only place a credential is created. `token` is returned to be displayed
    exactly once and then forgotten; only `secret_sha256` is ever persisted, so
    a stolen database yields no working credential.
    """

    key_id = secrets.token_hex(KEY_ID_BYTES)
    secret = secrets.token_urlsafe(SECRET_BYTES)
    return GeneratedKey(
        key_id=key_id,
        token=f"{PREFIX}_{key_id}_{secret}",
        secret_sha256=hash_secret(secret),
    )


def hash_secret(secret: str) -> str:
    """The stored verifier for a secret.

    SHA-256, not a password KDF, and the reasoning is ADR-024's: the input is
    256 bits of CSPRNG output, so there is nothing to slow down a search of.
    """

    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def parse(token: str) -> PresentedKey | None:
    """Split a presented token, or None if it is not one.

    `maxsplit=2` matters: `token_urlsafe` emits `-` and `_`, so the secret can
    contain underscores and only the first two separators are structural.
    """

    parts = token.split("_", 2)
    if len(parts) != 3:
        return None
    prefix, key_id, secret = parts
    if prefix != PREFIX or len(key_id) != KEY_ID_LENGTH or not secret:
        return None
    # A key_id that is not lowercase hex cannot exist in the store, and
    # rejecting it here keeps non-hex text out of the query and the logs.
    if any(character not in "0123456789abcdef" for character in key_id):
        return None
    return PresentedKey(key_id=key_id, secret=secret)


def matches(secret: str, expected_sha256: str) -> bool:
    """Constant-time comparison of a presented secret against a stored digest."""

    return hmac.compare_digest(hash_secret(secret), expected_sha256)


def absorb_miss(secret: str) -> None:
    """Do the work of a comparison that cannot succeed.

    Called when no key matched the presented `key_id`, so that the miss path
    costs what the hit path costs. Discarding the result is the point.
    """

    hmac.compare_digest(hash_secret(secret), _DUMMY_DIGEST)
