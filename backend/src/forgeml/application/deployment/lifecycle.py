"""Version build/start/stop use cases (docs 03/04; Module 5).

This service turns an accepted package into a running version by driving the
runtime through the lifecycle: build the image, start the container, reach
READY -- or FAIL the attempt with a safe diagnosis. It never holds a database
transaction across runtime work (docs 04): every build/start/stop happens
between committed transactions, and intent is persisted before the side effect.

Execution is inline, exactly as package validation is (Module 3, decision D-1):
the durable operation is created and completed in-process. Because that
operation is durable, idempotent, and correlated, moving execution behind a
background worker later needs no change to the HTTP contract -- the operation
would simply carry its inputs and be claimed by `claim_next` instead of run
here. That worker daemon remains deferred (ADR-006/ADR-010).

Activation and reconciliation are separate services; this one owns the path a
version takes from an accepted package to a stopped container.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from forgeml.application.deployment.support import (
    UNAVAILABLE,
    OperationAwareService,
    UnitOfWorkFactory,
    invalid_transition,
    latest_contract,
    missing,
    not_accepted,
)
from forgeml.domain.audit.models import AuditEvent
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
from forgeml.domain.identity.models import Principal
from forgeml.domain.operations.models import Operation, OperationFailure, OperationType
from forgeml.domain.package.generator import generate
from forgeml.domain.package.models import InferenceContract


def _deploy_fingerprint(package_id: UUID, policy: ResourcePolicy) -> str:
    parts = (
        str(package_id),
        str(policy.cpu_millicores),
        str(policy.memory_mib),
        str(policy.pids_limit),
    )
    return hashlib.sha256("\x00".join(parts).encode()).hexdigest()


class DeploymentLifecycleService(OperationAwareService):
    """Creates deployments and drives a version from build to stop."""

    def __init__(
        self, unit_of_work: UnitOfWorkFactory, runtime: RuntimeManager
    ) -> None:
        super().__init__(unit_of_work)
        self._runtime = runtime

    # -- commands ----------------------------------------------------------

    def create_deployment(
        self, name: str, correlation_id: UUID, principal: Principal
    ) -> Deployment:
        with self._unit_of_work() as uow:
            deployment = uow.deployments.create_deployment(name, DesiredState.RUNNING)
            uow.audit.record(
                AuditEvent(
                    actor_type=principal.actor_type,
                    actor_id=principal.actor_id,
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
        principal: Principal,
    ) -> Operation:
        """Build and start a new version of an accepted package."""

        with self._unit_of_work() as uow:
            if uow.deployments.find_deployment(deployment_id) is None:
                raise missing("deployment")
            package = uow.packages.find_by_id(package_id)
            if package is None:
                raise missing("package")
            contract = latest_contract(uow, package_id)
            if contract is None:
                raise not_accepted()
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
            principal,
        )

    def stop_version(
        self,
        version_id: UUID,
        idempotency_key: str,
        correlation_id: UUID,
        principal: Principal,
    ) -> Operation:
        """Stop a READY version and remove its container."""

        with self._unit_of_work() as uow:
            version = uow.deployments.find_version(version_id)
            if version is None:
                raise missing("deployment_version")
            if not can_transition(version.state, VersionState.STOPPED):
                raise invalid_transition(version.state, "stopped")
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

        return self._execute_stop(operation.id, version_id, correlation_id, principal)

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
        principal: Principal | None = None,
    ) -> Operation:
        version = self._claim_and_create_version(
            operation_id, deployment_id, package_id, policy, correlation_id, principal
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
                operation_id, version, UNAVAILABLE, correlation_id, principal
            )
        except RuntimeExecutionError as error:
            return self._fail_attempt(
                operation_id, version, error.failure, correlation_id, principal
            )

        version = mark_built(version, image_ref=image.image_ref)
        self._save_version(version)

        try:
            container = self._runtime.start(version.id, image, policy)
        except RuntimeUnavailable:
            return self._fail_attempt(
                operation_id, version, UNAVAILABLE, correlation_id, principal
            )
        except RuntimeExecutionError as error:
            return self._fail_attempt(
                operation_id, version, error.failure, correlation_id, principal
            )

        version = mark_ready(
            version, container_id=container.container_id, endpoint=container.endpoint
        )
        with self._unit_of_work() as uow:
            uow.deployments.save_version(version)
            uow.audit.record(self._event("ready", version, correlation_id, principal))
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
        principal: Principal | None = None,
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
            uow.audit.record(
                self._event("building", version, correlation_id, principal)
            )
            uow.commit()
            return version

    def _execute_stop(
        self,
        operation_id: UUID,
        version_id: UUID,
        correlation_id: UUID,
        principal: Principal | None = None,
    ) -> Operation:
        with self._unit_of_work() as uow:
            if uow.operations.claim(operation_id) is None:
                return self._current(operation_id)
            version = uow.deployments.find_version(version_id)
            uow.commit()
        if version is None:  # pragma: no cover - existence checked before begin
            return self._fail_operation(operation_id, UNAVAILABLE)

        # Docs 04: the route is removed *before* the container stops, so a
        # prediction never resolves to a version about to disappear. Clearing it
        # takes the deployment lock and is a no-op unless this version holds it.
        with self._unit_of_work() as uow:
            deployment = uow.deployments.lock_deployment(version.deployment_id)
            if deployment is not None and deployment.active_version_id == version_id:
                uow.deployments.save_deployment(
                    replace(deployment, active_version_id=None)
                )
            uow.commit()

        try:
            if version.container_id is not None:
                self._runtime.stop(version.container_id)
        except RuntimeUnavailable:
            return self._fail_operation(operation_id, UNAVAILABLE)

        stopped = mark_stopped(version)
        with self._unit_of_work() as uow:
            uow.deployments.save_version(stopped)
            uow.audit.record(self._event("stopped", stopped, correlation_id, principal))
            completed = uow.operations.complete(
                operation_id,
                {"version_id": str(stopped.id), "state": stopped.state.value},
            )
            uow.commit()
            return completed

    def _fail_attempt(
        self,
        operation_id: UUID,
        version: DeploymentVersion,
        failure: OperationFailure,
        correlation_id: UUID,
        principal: Principal | None = None,
    ) -> Operation:
        failed_version = mark_failed(version, failure)
        with self._unit_of_work() as uow:
            uow.deployments.save_version(failed_version)
            uow.audit.record(
                self._event("failed", failed_version, correlation_id, principal)
            )
            failed = uow.operations.fail(operation_id, failure)
            uow.commit()
            return failed
