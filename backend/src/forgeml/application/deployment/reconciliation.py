"""Runtime reconciliation (docs 04/11; ADR-004).

Metadata holds desired state; Docker holds observed state. They drift -- a
container dies, an operator removes one by hand, a crash leaves a resource
behind. Reconciliation compares the two and records every mismatch.

It records and never repairs. Docs 11 forbids automatically deleting a runtime
resource the platform does not recognise: an unknown container is exactly as
likely to be someone else's as it is to be ForgeML's litter, and the audit trail
is the safe answer to both.
"""

from __future__ import annotations

from uuid import UUID

from forgeml.application.deployment.support import (
    UNAVAILABLE,
    OperationAwareService,
    UnitOfWorkFactory,
)
from forgeml.domain.audit.models import ActorType, AuditEvent
from forgeml.domain.deployment.models import DeploymentVersion
from forgeml.domain.deployment.ports import RuntimeManager, RuntimeUnavailable
from forgeml.domain.operations.models import Operation, OperationType


def _mismatch_reason(version: DeploymentVersion | None, healthy: bool) -> str | None:
    if version is None:
        return "unknown_runtime"
    if not healthy:
        return "unhealthy_runtime"
    return None


class ReconciliationService(OperationAwareService):
    """Compares runtime resources against records and records mismatches."""

    def __init__(
        self, unit_of_work: UnitOfWorkFactory, runtime: RuntimeManager
    ) -> None:
        super().__init__(unit_of_work)
        self._runtime = runtime

    def reconcile(self, idempotency_key: str, correlation_id: UUID) -> Operation:
        """Compare runtime resources against records and record mismatches."""

        with self._unit_of_work() as uow:
            operation = uow.operations.begin(
                idempotency_key=idempotency_key,
                type=OperationType.DEPLOYMENT_RECONCILE,
                target_id="system",
                request_fingerprint="reconcile",
                correlation_id=correlation_id,
            )
            if operation.state.is_terminal:
                return operation
            uow.commit()

        return self._execute_reconcile(operation.id, correlation_id)

    def _execute_reconcile(self, operation_id: UUID, correlation_id: UUID) -> Operation:
        with self._unit_of_work() as uow:
            if uow.operations.claim(operation_id) is None:
                return self._current(operation_id)
            uow.commit()

        try:
            observed = self._runtime.reconcile()
        except RuntimeUnavailable:
            return self._fail_operation(operation_id, UNAVAILABLE)

        mismatches = 0
        with self._unit_of_work() as uow:
            for managed in observed:
                version = (
                    uow.deployments.find_version(managed.version_id)
                    if managed.version_id is not None
                    else None
                )
                reason = _mismatch_reason(version, managed.status.healthy)
                if reason is not None:
                    mismatches += 1
                    # Never auto-delete an unknown resource (docs 11); record it.
                    uow.audit.record(
                        AuditEvent(
                            actor_type=ActorType.SYSTEM,
                            action=f"deployment.reconcile.{reason}",
                            target_type="runtime",
                            target_id=managed.container_id,
                            correlation_id=correlation_id,
                            metadata={"version_id": str(managed.version_id)},
                        )
                    )
            completed = uow.operations.complete(
                operation_id,
                {"observed": str(len(observed)), "mismatches": str(mismatches)},
            )
            uow.commit()
            return completed
