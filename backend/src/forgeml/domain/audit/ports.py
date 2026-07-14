"""The audit trail port (docs 04)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from forgeml.domain.audit.models import AuditEvent


class AuditLog(Protocol):
    """Append-only audit trail.

    `record` enlists in the caller's unit of work, because docs 04 requires the
    audit record to live in the same transaction as the state change it
    describes. An audit event that could be committed separately would be a
    record of something that might not have happened.
    """

    def record(self, event: AuditEvent) -> None:
        """Append one audit event to the current transaction."""

    def for_target(self, target_id: str, limit: int) -> Sequence[AuditEvent]:
        """Read the audit trail of one target, newest first."""

    def for_correlation(self, correlation_id: UUID) -> Sequence[AuditEvent]:
        """Read every event recorded under one correlation ID."""
