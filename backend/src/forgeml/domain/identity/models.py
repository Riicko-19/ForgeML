"""Identity values (ADR-023).

A `Principal` is *who*, never *how they proved it*. It holds no credential, no
secret, no token, and no transport detail, which is what makes it safe to log,
safe to put in an append-only audit row, and safe to pass into the domain.

There is no anonymous principal. An unauthenticated route simply has no
principal, and its handler takes none. A singleton `ANONYMOUS` would type-check
everywhere an authenticated principal is expected; `None` cannot, so the absence
of identity is a compile-time error rather than a runtime value with weak
privileges.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

_MAX_ACTOR_ID = 64
_MAX_NAME = 128


class ActorType(StrEnum):
    """Who caused a state change.

    Two members, deliberately (ADR-023). An API-key holder is an `OPERATOR`
    whether it is a person or a CI pipeline, because ForgeML cannot yet tell
    them apart and a distinction it cannot verify would be a claim the
    append-only audit trail carries forever. `SYSTEM` covers reconciliation and
    startup recovery, which have no principal and must not invent one.
    """

    OPERATOR = "operator"
    SYSTEM = "system"


class AuthenticationMethod(StrEnum):
    """How a principal was established.

    One member today. A future `JWT` or `OIDC` verifier adds a member here and
    implements `CredentialVerifier`; nothing else in the identity model moves.
    """

    API_KEY = "api_key"


def safe_identifier(value: str, limit: int, label: str) -> str:
    """Bound a value and reject control characters.

    Identity values reach logs and audit rows, so they are held to the same rule
    the audit fields already use: bounded length, no control characters, no
    exceptions for internal callers.
    """

    if not 1 <= len(value) <= limit:
        raise ValueError(f"{label} must contain 1 to {limit} characters")
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ValueError(f"{label} must not contain control characters")
    return value


@dataclass(frozen=True, slots=True)
class Principal:
    """Who is acting.

    `actor_id` is stable and opaque, and for an API key it is the key's public
    `key_id` (ADR-024) -- an identifier that is not secret by construction, so
    recording it in an audit row leaks nothing.
    """

    actor_type: ActorType
    actor_id: str

    def __post_init__(self) -> None:
        safe_identifier(self.actor_id, _MAX_ACTOR_ID, "actor_id")


@dataclass(frozen=True, slots=True)
class AuthenticationContext:
    """The result of authenticating: who, plus which credential proved it.

    "Who acted" and "which credential was used" are different questions, and
    only the second one is useful during a key rotation or a compromise review.
    The application layer receives the `Principal`; the audit trail can record
    both.
    """

    principal: Principal
    credential_id: UUID
    method: AuthenticationMethod


@dataclass(frozen=True, slots=True)
class ApiKey:
    """A stored API-key record. Never carries the secret (ADR-024).

    Only `secret_sha256` is persisted, so this record cannot be turned back into
    a working credential -- which is the property that matters when the database
    is what leaks.
    """

    id: UUID
    key_id: str
    name: str
    secret_sha256: str
    created_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None

    def __post_init__(self) -> None:
        safe_identifier(self.key_id, _MAX_ACTOR_ID, "key_id")
        safe_identifier(self.name, _MAX_NAME, "name")

    def is_usable(self, now: datetime) -> bool:
        """Whether this key may authenticate a request at `now`.

        Revocation and expiry are separate states with one shared outcome. The
        caller is never told which applied (ADR-025): "this key exists but is
        revoked" is information an attacker can use, and the operator who needs
        it has the CLI.
        """

        if self.revoked_at is not None:
            return False
        return not (self.expires_at is not None and self.expires_at <= now)

    def principal(self) -> Principal:
        """The principal this key authenticates as."""

        return Principal(actor_type=ActorType.OPERATOR, actor_id=self.key_id)
