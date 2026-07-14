"""Package upload, validation, and read use cases.

Validation runs inside the request rather than on a worker. ADR-006 requires the
operation record to be durable and idempotent, which it is; ADR-010's worker
arrives with the deployment module, and validation is bounded in-process work
that needs no Docker. Leaving operations PENDING with nothing to execute them
would be a broken system, not a deferral.

The durable operation resource is exactly what lets execution move to the worker
later without changing the HTTP contract.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import BinaryIO
from uuid import UUID

from forgeml.application.unit_of_work import UnitOfWork
from forgeml.core.config import PackageLimits
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.audit.models import ActorType, AuditEvent
from forgeml.domain.operations.models import (
    Operation,
    OperationFailure,
    OperationType,
)
from forgeml.domain.package.models import (
    ArchiveUnreadable,
    Package,
    PackageValidation,
    ValidationState,
)
from forgeml.domain.package.ports import ArchiveReader, ArtifactStore, PackagePage
from forgeml.domain.package.rules import unreadable_archive
from forgeml.domain.package.rules import validate_package as apply_rules

UnitOfWorkFactory = Callable[[], UnitOfWork]


@dataclass(frozen=True, slots=True)
class PackageDetail:
    """A package together with its most recent validation verdict."""

    package: Package
    validation: PackageValidation | None


def _fingerprint(sha256: str, filename: str) -> str:
    # Docs 04: the upload fingerprint covers the computed checksum and the
    # declared upload metadata, so reusing a key for different bytes conflicts.
    return hashlib.sha256(f"{sha256}\x00{filename}".encode()).hexdigest()


class PackageService:
    """Uploads, validates, and reads packages."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkFactory,
        store: ArtifactStore,
        reader: ArchiveReader,
        limits: PackageLimits,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._store = store
        self._reader = reader
        self._limits = limits

    def upload(
        self,
        stream: BinaryIO,
        filename: str,
        idempotency_key: str,
        correlation_id: UUID,
    ) -> Operation:
        """Store an archive, validate it, and return its durable operation."""

        stored = self._store.put(stream, self._limits)
        fingerprint = _fingerprint(stored.sha256, filename)

        with self._unit_of_work() as uow:
            operation = uow.operations.begin(
                idempotency_key=idempotency_key,
                type=OperationType.PACKAGE_VALIDATE,
                target_id=stored.sha256,
                request_fingerprint=fingerprint,
                correlation_id=correlation_id,
            )
            if operation.state.is_terminal:
                # A replayed request. The work is already done; returning the
                # original operation is the whole point of the idempotency key.
                return operation

            package = uow.packages.get_or_create(
                sha256=stored.sha256,
                filename=filename,
                size_bytes=stored.size_bytes,
                artifact_uri=stored.uri,
            )
            uow.audit.record(
                AuditEvent(
                    actor_type=ActorType.OPERATOR,
                    action="package.uploaded",
                    target_type="package",
                    target_id=str(package.id),
                    correlation_id=correlation_id,
                    metadata={"sha256": package.sha256},
                )
            )
            uow.commit()

        return self._execute(operation.id, package.id, correlation_id)

    def _execute(
        self, operation_id: UUID, package_id: UUID, correlation_id: UUID
    ) -> Operation:
        """Claim the operation, validate, and record the verdict atomically."""

        with self._unit_of_work() as uow:
            claimed = uow.operations.claim(operation_id)
            if claimed is None:
                # A duplicate request already holds it. Report its state rather
                # than validating the same archive twice.
                current = uow.operations.get(operation_id)
                if current is None:  # pragma: no cover - it was just created
                    raise self._missing_operation()
                return current
            uow.commit()

        # Validation reads the artifact. Docs 04 forbids holding a database
        # transaction across that work, so the transaction is closed first.
        validation = self._validate(package_id)

        with self._unit_of_work() as uow:
            if validation is None:
                failed = uow.operations.fail(
                    operation_id,
                    OperationFailure(
                        code="artifact_unreadable",
                        message="the stored artifact could not be read",
                    ),
                )
                uow.commit()
                return failed

            uow.packages.save_validation(package_id, validation)
            uow.audit.record(
                AuditEvent(
                    actor_type=ActorType.SYSTEM,
                    action=f"package.{validation.state.value}",
                    target_type="package",
                    target_id=str(package_id),
                    correlation_id=correlation_id,
                    metadata={"findings": str(len(validation.findings))},
                )
            )
            # The operation succeeds because the validation *ran*. A rejected
            # package is a verdict, not a platform failure; the client reads the
            # findings from the package (docs 12 FR-01/FR-03).
            completed = uow.operations.complete(
                operation_id,
                {
                    "package_id": str(package_id),
                    "validation_state": validation.state.value,
                },
            )
            uow.commit()
            return completed

    def _validate(self, package_id: UUID) -> PackageValidation | None:
        with self._unit_of_work() as uow:
            package = uow.packages.find_by_id(package_id)
        if package is None:  # pragma: no cover - created in the same request
            raise self._missing_package()

        try:
            with self._store.open(package.sha256) as stream:
                inspection = self._reader.inspect(stream, self._limits)
                return apply_rules(inspection, self._limits)
        except ArchiveUnreadable:
            return unreadable_archive()
        except AppError:
            # The artifact itself is gone or unreadable: that is a platform
            # failure, not a package verdict, so the operation must fail.
            return None

    def get(self, package_id: UUID) -> PackageDetail:
        with self._unit_of_work() as uow:
            package = uow.packages.find_by_id(package_id)
            if package is None:
                raise self._missing_package()
            history = uow.packages.findings_for(package_id)
        return PackageDetail(package=package, validation=_latest(history))

    def list(self, limit: int, cursor: str | None) -> PackagePage:
        with self._unit_of_work() as uow:
            return uow.packages.list(limit=limit, cursor=cursor)

    @staticmethod
    def _missing_package() -> AppError:
        return AppError(
            category=ErrorCategory.NOT_FOUND,
            code="package_not_found",
            message="the referenced package does not exist",
        )

    @staticmethod
    def _missing_operation() -> AppError:
        return AppError(
            category=ErrorCategory.NOT_FOUND,
            code="operation_not_found",
            message="the referenced operation does not exist",
        )


def _latest(history: Sequence[PackageValidation]) -> PackageValidation | None:
    """The newest verdict. `findings_for` returns newest first."""

    return history[0] if history else None


def is_accepted(validation: PackageValidation | None) -> bool:
    """Only an accepted package may be deployed (docs 04)."""

    return validation is not None and validation.state is ValidationState.VALIDATED
