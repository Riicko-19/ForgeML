"""Deployment lifecycle use cases (docs 03/04; Module 5).

The service turns an accepted package into a running version by driving the
runtime through the lifecycle: build the image, start the container, reach
READY -- or FAIL the attempt with a safe diagnosis. It never holds a database
transaction across runtime work (docs 04): every build/start/stop happens
between committed transactions, and intent is persisted before the side effect.

Execution is inline, exactly as package validation is (Module 3, decision D-1):
the durable operation is created and completed in-process. Because that
operation is durable, idempotent, and correlated, moving execution behind a
background worker later needs no change to the HTTP contract -- the operation
would simply carry its inputs and be claimed by `claim_next` instead of run
here. That worker daemon is the one deferred piece of this module.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from forgeml.application.package.services import is_accepted
from forgeml.application.unit_of_work import UnitOfWork
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.audit.models import ActorType, AuditEvent
from forgeml.domain.deployment.models import (
    Deployment,
    DeploymentVersion,
    DesiredState,
    ResourcePolicy,
    VersionState,
)
from forgeml.domain.deployment.ports import (
    RuntimeExecutionError,
    RuntimeManager,
    RuntimeUnavailable,
)
from forgeml.domain.deployment.rules import (
    can_transition,
    mark_built,
    mark_failed,
    mark_ready,
    mark_stopped,
)
from forgeml.domain.operations.models import (
    Operation,
    OperationFailure,
    OperationType,
)
from forgeml.domain.package.generator import generate
from forgeml.domain.package.models import InferenceContract

UnitOfWorkFactory = Callable[[], UnitOfWork]

_UNAVAILABLE = OperationFailure(
    code="runtime_unavailable",
    message="the container runtime is unavailable; retry the operation",
)


def _deploy_fingerprint(package_id: UUID, policy: ResourcePolicy) -> str:
    parts = (
        str(package_id),
        str(policy.cpu_millicores),
        str(policy.memory_mib),
        str(policy.pids_limit),
    )
    return hashlib.sha256("\x00".join(parts).encode()).hexdigest()


class DeploymentService:
    """Creates deployments and drives version build/start/stop/reconcile."""

    def __init__(
        self, unit_of_work: UnitOfWorkFactory, runtime: RuntimeManager
    ) -> None:
        self._unit_of_work = unit_of_work
        self._runtime = runtime

    # -- commands ----------------------------------------------------------

    def create_deployment(self, name: str, correlation_id: UUID) -> Deployment:
        with self._unit_of_work() as uow:
            deployment = uow.deployments.create_deployment(name, DesiredState.RUNNING)
            uow.audit.record(
                AuditEvent(
                    actor_type=ActorType.OPERATOR,
                    action="deployment.created",
                    target_type="deployment",
                    target_id=str(deployment.id),
                    correlation_id=correlation_id,
                    metadata={"name": name},
                )
            )
            uow.commit()
        return deployment

    def deploy_version(
        self,
        deployment_id: UUID,
        package_id: UUID,
        resource_policy: ResourcePolicy,
        idempotency_key: str,
        correlation_id: UUID,
    ) -> Operation:
        """Build and start a new version of an accepted package."""

        with self._unit_of_work() as uow:
            if uow.deployments.find_deployment(deployment_id) is None:
                raise self._missing("deployment")
            package = uow.packages.find_by_id(package_id)
            if package is None:
                raise self._missing("package")
            contract = _latest_contract(uow, package_id)
            if contract is None:
                raise self._not_accepted()
            operation = uow.operations.begin(
                idempotency_key=idempotency_key,
                type=OperationType.DEPLOYMENT_VERSION_DEPLOY,
                target_id=str(deployment_id),
                request_fingerprint=_deploy_fingerprint(package_id, resource_policy),
                correlation_id=correlation_id,
            )
            if operation.state.is_terminal:
                return operation
            checksum = package.sha256
            uow.commit()

        return self._execute_deploy(
            operation.id,
            deployment_id,
            package_id,
            resource_policy,
            contract,
            checksum,
            correlation_id,
        )

    def stop_version(
        self, version_id: UUID, idempotency_key: str, correlation_id: UUID
    ) -> Operation:
        """Stop a READY version and remove its container."""

        with self._unit_of_work() as uow:
            version = uow.deployments.find_version(version_id)
            if version is None:
                raise self._missing("deployment_version")
            if not can_transition(version.state, VersionState.STOPPED):
                raise self._invalid_transition(version.state)
            operation = uow.operations.begin(
                idempotency_key=idempotency_key,
                type=OperationType.DEPLOYMENT_VERSION_STOP,
                target_id=str(version_id),
                request_fingerprint=str(version_id),
                correlation_id=correlation_id,
            )
            if operation.state.is_terminal:
                return operation
            uow.commit()

        return self._execute_stop(operation.id, version_id, correlation_id)

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

    # -- execution ---------------------------------------------------------

    def _execute_deploy(
        self,
        operation_id: UUID,
        deployment_id: UUID,
        package_id: UUID,
        policy: ResourcePolicy,
        contract: InferenceContract,
        checksum: str,
        correlation_id: UUID,
    ) -> Operation:
        version = self._claim_and_create_version(
            operation_id, deployment_id, package_id, policy, correlation_id
        )
        if version is None:
            return self._current(operation_id)

        # Build and start run outside any transaction (docs 04). Intent (the
        # image reference) is persisted the moment it is known.
        context = generate(contract, checksum=checksum)
        try:
            image = self._runtime.build(version.id, context, checksum, policy)
        except RuntimeUnavailable:
            return self._fail_attempt(
                operation_id, version, _UNAVAILABLE, correlation_id
            )
        except RuntimeExecutionError as error:
            return self._fail_attempt(
                operation_id, version, error.failure, correlation_id
            )

        version = mark_built(version, image_ref=image.image_ref)
        self._save_version(version)

        try:
            container = self._runtime.start(version.id, image, policy)
        except RuntimeUnavailable:
            return self._fail_attempt(
                operation_id, version, _UNAVAILABLE, correlation_id
            )
        except RuntimeExecutionError as error:
            return self._fail_attempt(
                operation_id, version, error.failure, correlation_id
            )

        version = mark_ready(
            version, container_id=container.container_id, endpoint=container.endpoint
        )
        with self._unit_of_work() as uow:
            uow.deployments.save_version(version)
            uow.audit.record(self._event("ready", version, correlation_id))
            completed = uow.operations.complete(
                operation_id,
                {"version_id": str(version.id), "state": version.state.value},
            )
            uow.commit()
            return completed

    def _claim_and_create_version(
        self,
        operation_id: UUID,
        deployment_id: UUID,
        package_id: UUID,
        policy: ResourcePolicy,
        correlation_id: UUID,
    ) -> DeploymentVersion | None:
        with self._unit_of_work() as uow:
            if uow.operations.claim(operation_id) is None:
                # A duplicate in-flight request already holds it: create no
                # second version and let the caller report the current state.
                return None
            attempt = uow.deployments.next_attempt(deployment_id, package_id)
            version = DeploymentVersion(
                id=uuid4(),
                deployment_id=deployment_id,
                package_id=package_id,
                attempt=attempt,
                state=VersionState.BUILDING,
                resource_policy=policy,
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )
            uow.deployments.add_version(version)
            uow.audit.record(self._event("building", version, correlation_id))
            uow.commit()
            return version

    def _execute_stop(
        self, operation_id: UUID, version_id: UUID, correlation_id: UUID
    ) -> Operation:
        with self._unit_of_work() as uow:
            if uow.operations.claim(operation_id) is None:
                return self._current(operation_id)
            version = uow.deployments.find_version(version_id)
            uow.commit()
        if version is None:  # pragma: no cover - existence checked before begin
            return self._fail_operation(operation_id, _UNAVAILABLE)

        try:
            if version.container_id is not None:
                self._runtime.stop(version.container_id)
        except RuntimeUnavailable:
            return self._fail_operation(operation_id, _UNAVAILABLE)

        stopped = mark_stopped(version)
        with self._unit_of_work() as uow:
            uow.deployments.save_version(stopped)
            uow.audit.record(self._event("stopped", stopped, correlation_id))
            completed = uow.operations.complete(
                operation_id,
                {"version_id": str(stopped.id), "state": stopped.state.value},
            )
            uow.commit()
            return completed

    def _execute_reconcile(self, operation_id: UUID, correlation_id: UUID) -> Operation:
        with self._unit_of_work() as uow:
            if uow.operations.claim(operation_id) is None:
                return self._current(operation_id)
            uow.commit()

        try:
            observed = self._runtime.reconcile()
        except RuntimeUnavailable:
            return self._fail_operation(operation_id, _UNAVAILABLE)

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

    # -- helpers -----------------------------------------------------------

    def _save_version(self, version: DeploymentVersion) -> None:
        with self._unit_of_work() as uow:
            uow.deployments.save_version(version)
            uow.commit()

    def _fail_attempt(
        self,
        operation_id: UUID,
        version: DeploymentVersion,
        failure: OperationFailure,
        correlation_id: UUID,
    ) -> Operation:
        failed_version = mark_failed(version, failure)
        with self._unit_of_work() as uow:
            uow.deployments.save_version(failed_version)
            uow.audit.record(self._event("failed", failed_version, correlation_id))
            failed = uow.operations.fail(operation_id, failure)
            uow.commit()
            return failed

    def _fail_operation(
        self, operation_id: UUID, failure: OperationFailure
    ) -> Operation:
        with self._unit_of_work() as uow:
            failed = uow.operations.fail(operation_id, failure)
            uow.commit()
            return failed

    def _current(self, operation_id: UUID) -> Operation:
        with self._unit_of_work() as uow:
            current = uow.operations.get(operation_id)
        if current is None:  # pragma: no cover - it was just created
            raise self._missing("operation")
        return current

    @staticmethod
    def _event(
        action: str, version: DeploymentVersion, correlation_id: UUID
    ) -> AuditEvent:
        return AuditEvent(
            actor_type=ActorType.SYSTEM,
            action=f"deployment_version.{action}",
            target_type="deployment_version",
            target_id=str(version.id),
            correlation_id=correlation_id,
            metadata={"attempt": str(version.attempt)},
        )

    @staticmethod
    def _missing(what: str) -> AppError:
        return AppError(
            category=ErrorCategory.NOT_FOUND,
            code=f"{what}_not_found",
            message=f"the referenced {what.replace('_', ' ')} does not exist",
        )

    @staticmethod
    def _not_accepted() -> AppError:
        return AppError(
            category=ErrorCategory.CONFLICT,
            code="package_not_accepted",
            message="only a validated package can be deployed",
        )

    @staticmethod
    def _invalid_transition(state: VersionState) -> AppError:
        return AppError(
            category=ErrorCategory.CONFLICT,
            code="invalid_state_transition",
            message=f"a {state.value} version cannot be stopped",
        )


def _latest_contract(uow: UnitOfWork, package_id: UUID) -> InferenceContract | None:
    """The analyzed contract of an accepted package, or None if not deployable."""

    history = uow.packages.findings_for(package_id)
    latest = history[0] if history else None
    if not is_accepted(latest) or latest is None or latest.contract is None:
        return None
    return latest.contract


def _mismatch_reason(version: DeploymentVersion | None, healthy: bool) -> str | None:
    if version is None:
        return "unknown_runtime"
    if not healthy:
        return "unhealthy_runtime"
    return None
