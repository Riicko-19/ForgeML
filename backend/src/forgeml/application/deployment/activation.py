"""Version activation and rollback (docs 04/12; ADR-005).

A deployment has exactly one ACTIVE version, and it is the one the platform
route resolves to. Activation is the only command that moves that route.
Rollback is not a separate command: it is this command aimed at an earlier
version.

Two invariants shape the code below and neither may be relaxed without an ADR:

1. A version never becomes ACTIVE unless its runtime is present, running, and
   healthy. Health is rechecked here, outside any transaction (docs 04), so a
   failed activation leaves the previous ACTIVE version serving.
2. The route change is atomic. The previous active version steps down and the
   candidate takes the route inside one transaction, under the deployment row
   lock, or neither happens.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from forgeml.application.deployment.support import (
    NOT_HEALTHY,
    UNAVAILABLE,
    OperationAwareService,
    UnitOfWorkFactory,
    invalid_transition,
    missing,
)
from forgeml.domain.deployment.models import VersionState
from forgeml.domain.deployment.ports import RuntimeManager, RuntimeUnavailable
from forgeml.domain.deployment.rules import (
    can_transition,
    mark_active,
    mark_deactivated,
)
from forgeml.domain.operations.models import Operation, OperationFailure, OperationType


class ActivationService(OperationAwareService):
    """Makes a READY version the deployment's one ACTIVE version."""

    def __init__(
        self, unit_of_work: UnitOfWorkFactory, runtime: RuntimeManager
    ) -> None:
        super().__init__(unit_of_work)
        self._runtime = runtime

    def activate_version(
        self,
        deployment_id: UUID,
        version_id: UUID,
        idempotency_key: str,
        correlation_id: UUID,
    ) -> Operation:
        """Make a READY version the deployment's one ACTIVE version (docs 04).

        Rollback is the same command aimed at an earlier version.
        """

        with self._unit_of_work() as uow:
            deployment = uow.deployments.find_deployment(deployment_id)
            if deployment is None:
                raise missing("deployment")
            version = uow.deployments.find_version(version_id)
            if version is None or version.deployment_id != deployment_id:
                raise missing("deployment_version")
            if version.state is not VersionState.ACTIVE and not can_transition(
                version.state, VersionState.ACTIVE
            ):
                raise invalid_transition(version.state, "activated")
            operation = uow.operations.begin(
                idempotency_key=idempotency_key,
                type=OperationType.DEPLOYMENT_VERSION_ACTIVATE,
                target_id=str(version_id),
                request_fingerprint=str(version_id),
                correlation_id=correlation_id,
            )
            if operation.state.is_terminal:
                return operation
            uow.commit()

        return self._execute_activate(
            operation.id, deployment_id, version_id, correlation_id
        )

    def _execute_activate(
        self,
        operation_id: UUID,
        deployment_id: UUID,
        version_id: UUID,
        correlation_id: UUID,
    ) -> Operation:
        with self._unit_of_work() as uow:
            if uow.operations.claim(operation_id) is None:
                return self._current(operation_id)
            version = uow.deployments.find_version(version_id)
            uow.commit()
        if version is None:  # pragma: no cover - existence checked before begin
            return self._fail_operation(operation_id, UNAVAILABLE)

        # Invariant 1: health is rechecked outside any transaction (docs 04).
        if version.container_id is None:
            return self._fail_operation(operation_id, NOT_HEALTHY)
        try:
            status = self._runtime.inspect(version.container_id)
        except RuntimeUnavailable:
            return self._fail_operation(operation_id, UNAVAILABLE)
        if not (status.present and status.running and status.healthy):
            return self._fail_operation(operation_id, NOT_HEALTHY)

        # Invariant 2: the route change is atomic under the deployment lock.
        with self._unit_of_work() as uow:
            deployment = uow.deployments.lock_deployment(deployment_id)
            candidate = uow.deployments.find_version(version_id)
            if deployment is None or candidate is None:  # pragma: no cover
                return self._fail_operation(operation_id, UNAVAILABLE)
            if (
                candidate.state is VersionState.ACTIVE
                and deployment.active_version_id == version_id
            ):
                completed = uow.operations.complete(
                    operation_id,
                    {"version_id": str(version_id), "state": candidate.state.value},
                )
                uow.commit()
                return completed
            if not can_transition(candidate.state, VersionState.ACTIVE):
                failure = OperationFailure(
                    code="invalid_state_transition",
                    message=f"a {candidate.state.value} version cannot be activated",
                )
                failed = uow.operations.fail(operation_id, failure)
                uow.commit()
                return failed
            previous_id = deployment.active_version_id
            if previous_id is not None and previous_id != version_id:
                previous = uow.deployments.find_version(previous_id)
                if previous is not None and previous.state is VersionState.ACTIVE:
                    uow.deployments.save_version(mark_deactivated(previous))
            uow.deployments.save_version(mark_active(candidate))
            uow.deployments.save_deployment(
                replace(deployment, active_version_id=version_id)
            )
            uow.audit.record(self._event("activated", candidate, correlation_id))
            completed = uow.operations.complete(
                operation_id,
                {"version_id": str(version_id), "state": VersionState.ACTIVE.value},
            )
            uow.commit()
            return completed
