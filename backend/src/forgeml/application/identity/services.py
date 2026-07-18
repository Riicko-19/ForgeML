"""Credential verification and key administration (ADR-024, ADR-026).

`ApiKeyVerifier` implements the `CredentialVerifier` port. It knows about tokens
and stores; it knows nothing about HTTP. It receives a presented string, not a
header and not a request, which is what keeps the transport out of the
application layer (ADR-019).

`ApiKeyAdministration` is driven by the CLI, never by a route. Epic 1 has
authentication and no authorization, so an authenticated key-creation endpoint
would let every valid key mint more keys -- privilege escalation delivered as a
convenience feature (ADR-026).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from forgeml.application.unit_of_work import UnitOfWork
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.identity import credentials
from forgeml.domain.identity.models import (
    ApiKey,
    AuthenticationContext,
    AuthenticationMethod,
)

UnitOfWorkFactory = Callable[[], UnitOfWork]
Clock = Callable[[], datetime]

_LOGGER = logging.getLogger("forgeml.identity")


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ApiKeyVerifier:
    """Turns a presented API key into an authenticated identity, or nothing.

    Every failure returns `None` and logs a reason. The reason never reaches the
    client (ADR-025) -- distinguishing "unknown key" from "wrong secret" to a
    caller is an enumeration oracle -- but an operator debugging a broken
    deployment needs it, and the log is where they can have it safely.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWorkFactory,
        clock: Clock = _utc_now,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def verify(self, presented: str) -> AuthenticationContext | None:
        parsed = credentials.parse(presented)
        if parsed is None:
            _LOGGER.warning(
                "Authentication failed.",
                extra={"event": "authentication_failed", "reason": "malformed_token"},
            )
            return None

        with self._unit_of_work() as uow:
            key = uow.api_keys.find_by_key_id(parsed.key_id)

        if key is None:
            # Spend the same work a real comparison would, so that an unknown
            # key_id and a wrong secret are indistinguishable by latency.
            credentials.absorb_miss(parsed.secret)
            self._refuse("unknown_key", parsed.key_id)
            return None

        # The secret is checked before the key's state, so that a wrong secret
        # against a revoked key_id still costs a comparison. Checking state
        # first would let an attacker detect revocation by timing.
        secret_matches = credentials.matches(parsed.secret, key.secret_sha256)
        if not secret_matches:
            self._refuse("wrong_secret", parsed.key_id)
            return None
        if not key.is_usable(self._clock()):
            self._refuse(
                "revoked" if key.revoked_at is not None else "expired", parsed.key_id
            )
            return None

        self._touch(key.id)
        return AuthenticationContext(
            principal=key.principal(),
            credential_id=key.id,
            method=AuthenticationMethod.API_KEY,
        )

    def _refuse(self, reason: str, key_id: str) -> None:
        # key_id is safe to log: it is not secret by construction (ADR-024).
        # The presented secret is never logged, in any branch.
        _LOGGER.warning(
            "Authentication failed.",
            extra={
                "event": "authentication_failed",
                "reason": reason,
                "key_id": key_id,
            },
        )

    def _touch(self, credential_id: UUID) -> None:
        """Record the use, and never fail the request because it did not stick.

        This write is bookkeeping for compromise review. A database hiccup here
        must not turn a valid credential into a rejected one.
        """

        try:
            with self._unit_of_work() as uow:
                uow.api_keys.touch_last_used(credential_id, self._clock())
                uow.commit()
        except Exception:  # pragma: no cover - defensive; never fail auth on this
            _LOGGER.warning(
                "Could not record API key use.",
                extra={"event": "api_key_touch_failed"},
            )


class ApiKeyAdministration:
    """Key lifecycle, driven out-of-band by the CLI (ADR-026).

    Deliberately not reachable over HTTP. Its authorization is possession of the
    database credential and shell access on the host -- the same authority
    needed to run the control plane at all, so it grants nothing new.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWorkFactory,
        clock: Clock = _utc_now,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def create(self, name: str, expires_in_days: int | None = None) -> str:
        """Mint a key and return its token, which is displayed exactly once.

        Only the digest is stored, so this return value is the sole moment the
        credential exists in recoverable form (ADR-026).
        """

        now = self._clock()
        generated = credentials.generate()
        key = ApiKey(
            id=uuid4(),
            key_id=generated.key_id,
            name=name,
            secret_sha256=generated.secret_sha256,
            created_at=now,
            expires_at=(
                now + timedelta(days=expires_in_days)
                if expires_in_days is not None
                else None
            ),
        )
        with self._unit_of_work() as uow:
            uow.api_keys.create(key)
            uow.commit()
        _LOGGER.info(
            "API key created.",
            extra={
                "event": "api_key_created",
                "key_id": key.key_id,
                "name": key.name,
            },
        )
        return generated.token

    def list(self) -> Sequence[ApiKey]:
        """Every key, newest first. Secrets are not recoverable."""

        with self._unit_of_work() as uow:
            return uow.api_keys.list()

    def revoke(self, key_id: str) -> None:
        """Revoke a key. Takes effect on the next request; there is no cache."""

        with self._unit_of_work() as uow:
            revoked = uow.api_keys.revoke(key_id, self._clock())
            uow.commit()
        if not revoked:
            raise AppError(
                category=ErrorCategory.NOT_FOUND,
                code="api_key_not_found",
                message="the referenced api key does not exist",
            )
        _LOGGER.info(
            "API key revoked.",
            extra={"event": "api_key_revoked", "key_id": key_id},
        )
