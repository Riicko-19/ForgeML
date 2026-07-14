"""The durable operation store (ADR-006, ADR-010, ADR-016)."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from forgeml.domain.operations.models import (
    Operation,
    OperationFailure,
    OperationType,
)


class OperationStore(Protocol):
    """Durable operations, claimed by one worker at a time.

    This store is the queue (ADR-010: no external broker). Claiming uses row
    locking, so a second worker never takes a claimed row.
    """

    def begin(
        self,
        idempotency_key: str,
        type: OperationType,
        target_id: str,
        request_fingerprint: str,
        correlation_id: UUID,
    ) -> Operation:
        """Create the operation, or return the original one for a repeated request.

        The same key, type, and target with the same fingerprint returns the
        original operation unchanged. The same key with a different fingerprint
        raises AppError(CONFLICT, idempotency_conflict) — a client may not reuse
        a key for different work (docs 04).
        """

    def get(self, operation_id: UUID) -> Operation | None:
        """Read one operation."""

    def claim_next(
        self, types: tuple[OperationType, ...] | None = None
    ) -> Operation | None:
        """Claim the oldest pending operation, or None.

        `types` selects a lane. Without lanes a slow build would block a fast
        validation behind it, because both queue in one table (ADR-016).
        """

    def claim(self, operation_id: UUID) -> Operation | None:
        """Claim one named operation, or None if it is not pending.

        An inline executor must run *its own* operation. `claim_next` would take
        the oldest pending one instead, so under concurrent uploads a request
        would execute another request's work and report the wrong result.

        Returns None when the operation is absent or already claimed, which is
        how a duplicate in-flight request declines to run the same work twice.
        """

    def complete(self, operation_id: UUID, result: dict[str, Any]) -> Operation:
        """Terminally succeed a running operation."""

    def fail(self, operation_id: UUID, failure: OperationFailure) -> Operation:
        """Terminally fail a running operation."""

    def recover_orphaned(self) -> int:
        """Return operations abandoned by a dead worker to the queue (ADR-016).

        ADR-010 supervises exactly one worker, so at startup any RUNNING row is
        an orphan of the previous process. It returns to PENDING, or fails as
        `operation_abandoned` once it has exhausted its attempts. Returns the
        number of operations recovered.
        """
