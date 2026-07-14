"""In-memory implementations of the Module 2 ports.

Module 3 will test its use cases against these. That is only safe if they behave
like PostgreSQL, so they are held to the same conformance suite as the real
adapters (tests/contract/test_port_conformance.py) rather than being trusted to
be "close enough".
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import TracebackType
from typing import Any
from uuid import UUID, uuid4

from forgeml.application.unit_of_work import UnitOfWork
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.audit.models import AuditEvent
from forgeml.domain.operations.models import (
    MAX_ATTEMPTS,
    Operation,
    OperationFailure,
    OperationState,
    OperationType,
)
from forgeml.domain.package.models import (
    Package,
    PackageState,
    PackageValidation,
)
from forgeml.domain.package.ports import PackagePage


class _Clock:
    """Monotonic timestamps, so ordering is deterministic without sleeping."""

    def __init__(self) -> None:
        self._now = datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        self._now += timedelta(microseconds=1)
        return self._now


class InMemoryPackageCatalog:
    def __init__(self, clock: _Clock) -> None:
        self._clock = clock
        self._packages: dict[UUID, Package] = {}
        self._validations: dict[UUID, dict[str, PackageValidation]] = {}

    def get_or_create(
        self, sha256: str, filename: str, size_bytes: int, artifact_uri: str
    ) -> Package:
        existing = self.find_by_checksum(sha256)
        if existing is not None:
            return existing
        now = self._clock()
        package = Package(
            id=uuid4(),
            sha256=sha256,
            filename=filename,
            size_bytes=size_bytes,
            manifest_version=None,
            state=PackageState.DRAFT,
            artifact_uri=artifact_uri,
            created_at=now,
            updated_at=now,
        )
        self._packages[package.id] = package
        return package

    def find_by_id(self, package_id: UUID) -> Package | None:
        return self._packages.get(package_id)

    def find_by_checksum(self, sha256: str) -> Package | None:
        return next(
            (item for item in self._packages.values() if item.sha256 == sha256), None
        )

    def save_validation(self, package_id: UUID, validation: PackageValidation) -> None:
        package = self._packages.get(package_id)
        if package is None:
            raise AppError(
                category=ErrorCategory.NOT_FOUND,
                code="package_not_found",
                message="the referenced package does not exist",
            )
        history = self._validations.setdefault(package_id, {})
        history[validation.validator_version] = validation
        self._packages[package_id] = replace(
            package,
            state=PackageState.from_validation(validation.state),
            manifest=validation.manifest,
            manifest_version=(
                validation.manifest.forge_version
                if validation.manifest is not None
                else package.manifest_version
            ),
            updated_at=self._clock(),
        )

    def list(self, limit: int, cursor: str | None = None) -> PackagePage:
        ordered = sorted(
            self._packages.values(),
            key=lambda item: (item.created_at, item.id),
            reverse=True,
        )
        if cursor is not None:
            try:
                timestamp, identifier = cursor.split("|", 1)
                key = (datetime.fromisoformat(timestamp), UUID(identifier))
            except ValueError as error:
                raise AppError(
                    category=ErrorCategory.BAD_REQUEST,
                    code="cursor_invalid",
                    message="the supplied pagination cursor is not valid",
                ) from error
            ordered = [item for item in ordered if (item.created_at, item.id) < key]

        page = ordered[:limit]
        has_more = len(ordered) > limit
        next_cursor = (
            f"{page[-1].created_at.isoformat()}|{page[-1].id}" if has_more else None
        )
        return PackagePage(items=tuple(page), next_cursor=next_cursor)

    def findings_for(self, package_id: UUID) -> Sequence[PackageValidation]:
        return list(self._validations.get(package_id, {}).values())


class InMemoryOperationStore:
    def __init__(self, clock: _Clock) -> None:
        self._clock = clock
        self._operations: dict[UUID, Operation] = {}

    def begin(
        self,
        idempotency_key: str,
        type: OperationType,
        target_id: str,
        request_fingerprint: str,
        correlation_id: UUID,
    ) -> Operation:
        existing = self._by_key(idempotency_key, type, target_id)
        if existing is not None:
            if existing.request_fingerprint != request_fingerprint:
                raise AppError(
                    category=ErrorCategory.CONFLICT,
                    code="idempotency_conflict",
                    message=(
                        "this idempotency key was already used for a different request"
                    ),
                )
            return existing

        now = self._clock()
        operation = Operation(
            id=uuid4(),
            idempotency_key=idempotency_key,
            type=type,
            target_id=target_id,
            request_fingerprint=request_fingerprint,
            state=OperationState.PENDING,
            correlation_id=correlation_id,
            attempts=0,
            created_at=now,
            updated_at=now,
        )
        self._operations[operation.id] = operation
        return operation

    def get(self, operation_id: UUID) -> Operation | None:
        return self._operations.get(operation_id)

    def claim_next(
        self, types: tuple[OperationType, ...] | None = None
    ) -> Operation | None:
        candidates = sorted(
            (
                item
                for item in self._operations.values()
                if item.state is OperationState.PENDING
                and (types is None or item.type in types)
            ),
            key=lambda item: item.created_at,
        )
        if not candidates:
            return None
        claimed = replace(
            candidates[0],
            state=OperationState.RUNNING,
            claimed_at=self._clock(),
            attempts=candidates[0].attempts + 1,
        )
        self._operations[claimed.id] = claimed
        return claimed

    def claim(self, operation_id: UUID) -> Operation | None:
        operation = self._operations.get(operation_id)
        if operation is None or operation.state is not OperationState.PENDING:
            return None
        claimed = replace(
            operation,
            state=OperationState.RUNNING,
            claimed_at=self._clock(),
            attempts=operation.attempts + 1,
        )
        self._operations[operation_id] = claimed
        return claimed

    def complete(self, operation_id: UUID, result: dict[str, Any]) -> Operation:
        running = self._running(operation_id)
        done = replace(
            running,
            state=OperationState.SUCCEEDED,
            result=copy.deepcopy(result),
            completed_at=self._clock(),
        )
        self._operations[operation_id] = done
        return done

    def fail(self, operation_id: UUID, failure: OperationFailure) -> Operation:
        running = self._running(operation_id)
        done = replace(
            running,
            state=OperationState.FAILED,
            failure=failure,
            completed_at=self._clock(),
        )
        self._operations[operation_id] = done
        return done

    def recover_orphaned(self) -> int:
        orphans = [
            item
            for item in self._operations.values()
            if item.state is OperationState.RUNNING
        ]
        for orphan in orphans:
            if orphan.attempts >= MAX_ATTEMPTS:
                self._operations[orphan.id] = replace(
                    orphan,
                    state=OperationState.FAILED,
                    failure=OperationFailure(
                        code="operation_abandoned",
                        message="the operation was abandoned after repeated failures",
                    ),
                    completed_at=self._clock(),
                )
            else:
                self._operations[orphan.id] = replace(
                    orphan, state=OperationState.PENDING, claimed_at=None
                )
        return len(orphans)

    def _running(self, operation_id: UUID) -> Operation:
        operation = self._operations.get(operation_id)
        if operation is None:
            raise AppError(
                category=ErrorCategory.NOT_FOUND,
                code="operation_not_found",
                message="the referenced operation does not exist",
            )
        if operation.state is not OperationState.RUNNING:
            raise AppError(
                category=ErrorCategory.CONFLICT,
                code="invalid_state_transition",
                message=(
                    f"an operation in state {operation.state.value} "
                    "cannot be completed"
                ),
            )
        return operation

    def _by_key(
        self, idempotency_key: str, type: OperationType, target_id: str
    ) -> Operation | None:
        return next(
            (
                item
                for item in self._operations.values()
                if item.idempotency_key == idempotency_key
                and item.type is type
                and item.target_id == target_id
            ),
            None,
        )


class InMemoryAuditLog:
    def __init__(self, clock: _Clock) -> None:
        self._clock = clock
        self._events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        # The database assigns identity and time on append; a fake that returned
        # events without them would let Module 3 rely on a field PostgreSQL
        # populates and the fake does not.
        self._events.append(replace(event, id=uuid4(), occurred_at=self._clock()))

    def for_target(self, target_id: str, limit: int) -> Sequence[AuditEvent]:
        matching = [item for item in self._events if item.target_id == target_id]
        return list(reversed(matching))[:limit]

    def for_correlation(self, correlation_id: UUID) -> Sequence[AuditEvent]:
        return [item for item in self._events if item.correlation_id == correlation_id]

    def discard(self) -> None:
        self._events.clear()


class InMemoryUnitOfWork(UnitOfWork):
    """A unit of work whose rollback really does discard writes.

    Repositories write into a scratch copy; commit publishes it. A fake that
    committed on every write would hide exactly the bug the transaction tests
    exist to catch.
    """

    def __init__(self) -> None:
        self._clock = _Clock()
        self._committed = self._new_state()
        self.packages, self.operations, self.audit = self._committed

    def _new_state(
        self,
    ) -> tuple[InMemoryPackageCatalog, InMemoryOperationStore, InMemoryAuditLog]:
        return (
            InMemoryPackageCatalog(self._clock),
            InMemoryOperationStore(self._clock),
            InMemoryAuditLog(self._clock),
        )

    def __enter__(self) -> InMemoryUnitOfWork:
        self._scratch = copy.deepcopy(self._committed)
        self.packages, self.operations, self.audit = self._scratch
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.packages, self.operations, self.audit = self._committed

    def commit(self) -> None:
        self._committed = copy.deepcopy(self._scratch)

    def rollback(self) -> None:
        self._scratch = copy.deepcopy(self._committed)
        self.packages, self.operations, self.audit = self._scratch
