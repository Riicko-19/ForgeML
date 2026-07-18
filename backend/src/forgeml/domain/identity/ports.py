"""Ports the identity domain drives (ADR-024).

`CredentialVerifier` is the extension seam, and it is deliberately one Protocol
with one method. A future JWT or OIDC verifier implements it and is composed in
the composition root; the API layer, the application layer, and the identity
model are all unchanged by its arrival. The seam is the deliverable -- a plugin
framework would be the speculative generality the FEK forbids.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from forgeml.domain.identity.models import ApiKey, AuthenticationContext


class CredentialVerifier(Protocol):
    """Turns a presented credential into an authenticated identity, or nothing.

    Returns `None` for every failure -- unparseable, unknown, wrong, expired,
    revoked. The verifier does not distinguish them to its caller because the
    caller must not distinguish them to the client (ADR-025); the reason is
    logged where an operator can read it.
    """

    def verify(self, presented: str) -> AuthenticationContext | None:
        """Authenticate a presented credential."""


class ApiKeyStore(Protocol):
    """Durable API-key records.

    Note what is absent: no method returns a secret, because no secret is
    stored. `create` takes an already-hashed verifier, so the plaintext never
    reaches persistence in any code path.
    """

    def find_by_key_id(self, key_id: str) -> ApiKey | None:
        """Read one key by its public lookup handle."""

    def create(self, key: ApiKey) -> None:
        """Persist a new key record. A duplicate key_id raises CONFLICT."""

    def list(self) -> Sequence[ApiKey]:
        """Read every key, newest first. Secrets are not recoverable."""

    def revoke(self, key_id: str, revoked_at: datetime) -> bool:
        """Revoke a key. Returns False when no such key exists.

        Revoking an already-revoked key leaves the original timestamp: the first
        revocation is the one that mattered, and overwriting it would corrupt
        the incident timeline it exists to record.
        """

    def touch_last_used(self, key_id: UUID, used_at: datetime) -> None:
        """Record that a key authenticated a request.

        Written outside the request's own transaction so authentication never
        contends with the work it authorized. A lost write here costs a slightly
        stale timestamp, which is the right thing to trade for not putting a
        write on every read path.
        """
