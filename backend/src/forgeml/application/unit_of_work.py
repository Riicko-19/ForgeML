"""The transaction boundary owned by the application layer.

A use case opens one unit of work, mutates state through the repositories it
exposes, and commits once. Docs 04 requires the audit record for a state change
to live in the same transaction as the change itself, which is only expressible
if the repositories share one transaction — that is what this port guarantees.

This protocol lives in the application layer, not in core, because core cannot
import domain ports without creating a core <-> domain import cycle, and because
transactions are orchestrated by use cases rather than by domain policy.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol

from forgeml.domain.audit.ports import AuditLog
from forgeml.domain.operations.ports import OperationStore
from forgeml.domain.package.ports import PackageCatalog


class UnitOfWork(Protocol):
    """One atomic metadata transaction.

    Leaving the context without committing rolls back. A unit of work is never
    held across provider work: docs 04 forbids a database transaction spanning a
    Docker build, start, or stop.
    """

    packages: PackageCatalog
    operations: OperationStore
    audit: AuditLog

    def __enter__(self) -> UnitOfWork:
        """Begin the transaction."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit on a clean exit that called commit; otherwise roll back."""

    def commit(self) -> None:
        """Commit the transaction."""

    def rollback(self) -> None:
        """Roll back the transaction."""
