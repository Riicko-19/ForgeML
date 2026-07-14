"""Durable operation records (ADR-006).

An operation is the durable intent behind a long-running command. It is created
before any provider work begins, it is claimed by exactly one worker, and it
ends in a terminal state that never changes again.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

MAX_ATTEMPTS = 3


class OperationType(StrEnum):
    """The kinds of durable work the control plane performs.

    Only the package operations exist today. Build, start, stop, activate, and
    reconcile arrive with the modules that own them (ADR-006 names them; they
    are not declared here before they can be executed).
    """

    PACKAGE_VALIDATE = "package_validate"


class OperationState(StrEnum):
    """Operation lifecycle. SUCCEEDED and FAILED are terminal and immutable."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        return self in (OperationState.SUCCEEDED, OperationState.FAILED)


@dataclass(frozen=True, slots=True)
class OperationFailure:
    """A safe, classified failure. Never a trace, a host path, or a payload."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class Operation:
    """One durable unit of asynchronous work."""

    id: UUID
    idempotency_key: str
    type: OperationType
    target_id: str
    request_fingerprint: str
    state: OperationState
    correlation_id: UUID
    attempts: int
    created_at: datetime
    updated_at: datetime
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    failure: OperationFailure | None = None
