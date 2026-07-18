"""The deployment lifecycle, driven end to end against a fake runtime.

This is the Module 5 exit gate (docs 06): every transition, failure, retry, and
recovery branch, proven without Docker. The service is wired to the in-memory
unit of work and the scriptable FakeRuntimeManager, so a test can force a build
or start to fail, or Docker to be unavailable, and assert the resulting state.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from forgeml.application.deployment.services import DeploymentServices
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.deployment.models import (
    DeploymentVersion,
    ResourcePolicy,
    VersionState,
)
from forgeml.domain.operations.models import (
    Operation,
    OperationFailure,
    OperationState,
)
from forgeml.domain.package.analyzer import analyze
from forgeml.domain.package.generator import GeneratedBuildContext, generate
from forgeml.domain.package.models import (
    ManifestV1,
    PackageValidation,
    ValidationState,
)
from tests.fake_runtime import FakeRuntimeManager
from tests.fakes import InMemoryUnitOfWork
from tests.packages import VALID_MANIFEST
from tests.support import TEST_PRINCIPAL

POLICY = ResourcePolicy(cpu_millicores=500, memory_mib=256)
CORR = uuid4()


@pytest.fixture
def uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture
def runtime() -> FakeRuntimeManager:
    return FakeRuntimeManager()


@pytest.fixture
def service(uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager) -> DeploymentServices:
    return DeploymentServices.create(lambda: uow, runtime)


def _accept_package(uow: InMemoryUnitOfWork, *, accepted: bool = True) -> UUID:
    manifest = ManifestV1.model_validate(VALID_MANIFEST)
    with uow:
        package = uow.packages.get_or_create("a" * 64, "m.forge", 10, "artifact://a")
        validation = PackageValidation(
            state=ValidationState.VALIDATED if accepted else ValidationState.REJECTED,
            validator_version="1",
            findings=(),
            manifest=manifest if accepted else None,
            contract=analyze(manifest) if accepted else None,
        )
        uow.packages.save_validation(package.id, validation)
        uow.commit()
    return package.id


def _versions(
    uow: InMemoryUnitOfWork, deployment_id: UUID
) -> tuple[DeploymentVersion, ...]:
    with uow:
        return uow.deployments.list_versions(deployment_id)


def _deploy(
    service: DeploymentServices, deployment_id: UUID, package_id: UUID, key: str
) -> Operation:
    return service.lifecycle.deploy_version(
        deployment_id, package_id, POLICY, key, CORR, TEST_PRINCIPAL
    )


def test_deploy_walks_a_package_to_a_ready_version(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id

    operation = _deploy(service, deployment_id, package_id, "k1")

    assert operation.state is OperationState.SUCCEEDED
    assert operation.result is not None
    assert operation.result["state"] == "ready"

    (version,) = _versions(uow, deployment_id)
    assert version.state is VersionState.READY
    assert version.image_ref is not None
    assert version.container_id is not None
    assert version.endpoint is not None
    assert version.resource_policy.cpu_millicores == 500
    # The container the runtime started is the one recorded.
    assert [m.container_id for m in runtime.reconcile()] == [version.container_id]


def test_a_build_failure_fails_the_attempt(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    runtime.build_failure = OperationFailure(
        code="build_failed", message="dependency install failed"
    )
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id

    operation = _deploy(service, deployment_id, package_id, "k1")

    assert operation.state is OperationState.FAILED
    assert operation.failure is not None and operation.failure.code == "build_failed"
    (version,) = _versions(uow, deployment_id)
    assert version.state is VersionState.FAILED
    assert version.failure is not None and version.failure.code == "build_failed"
    assert version.image_ref is None
    # A failed build starts no container.
    assert runtime.reconcile() == ()


def test_a_start_failure_fails_the_attempt_after_the_image_is_recorded(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    runtime.start_failure = OperationFailure(
        code="readiness_timeout", message="the container never became healthy"
    )
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id

    operation = _deploy(service, deployment_id, package_id, "k1")

    assert operation.state is OperationState.FAILED
    assert operation.failure is not None
    assert operation.failure.code == "readiness_timeout"
    (version,) = _versions(uow, deployment_id)
    assert version.state is VersionState.FAILED
    # The image reference was persisted before the start was attempted (docs 04).
    assert version.image_ref is not None


def test_retry_after_a_failure_is_a_new_attempt_that_can_succeed(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id

    runtime.build_failure = OperationFailure(code="build_failed", message="install")
    first = _deploy(service, deployment_id, package_id, "k1")
    assert first.state is OperationState.FAILED

    runtime.build_failure = None
    second = _deploy(service, deployment_id, package_id, "k2")
    assert second.state is OperationState.SUCCEEDED

    versions = _versions(uow, deployment_id)
    assert [v.attempt for v in versions] == [2, 1]
    assert versions[0].state is VersionState.READY
    assert versions[1].state is VersionState.FAILED


def test_a_ready_version_can_be_stopped(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")

    (ready,) = _versions(uow, deployment_id)
    operation = service.lifecycle.stop_version(ready.id, "stop-1", CORR, TEST_PRINCIPAL)

    assert operation.state is OperationState.SUCCEEDED
    (version,) = _versions(uow, deployment_id)
    assert version.state is VersionState.STOPPED
    # The container was removed from the runtime.
    assert runtime.reconcile() == ()


def test_stopping_a_failed_version_is_an_invalid_transition(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    runtime.build_failure = OperationFailure(code="build_failed", message="x")
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")
    (failed,) = _versions(uow, deployment_id)

    with pytest.raises(AppError) as captured:
        service.lifecycle.stop_version(failed.id, "stop-1", CORR, TEST_PRINCIPAL)
    assert captured.value.category is ErrorCategory.CONFLICT
    assert captured.value.code == "invalid_state_transition"


def test_only_an_accepted_package_can_be_deployed(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    package_id = _accept_package(uow, accepted=False)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id

    with pytest.raises(AppError) as captured:
        _deploy(service, deployment_id, package_id, "k1")
    assert captured.value.code == "package_not_accepted"


def test_deploying_to_an_unknown_deployment_is_not_found(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    package_id = _accept_package(uow)
    with pytest.raises(AppError) as captured:
        _deploy(service, uuid4(), package_id, "k1")
    assert captured.value.category is ErrorCategory.NOT_FOUND


# -- activation, rollback, and the route (Module 7) ---------------------------


def _active_version_id(uow: InMemoryUnitOfWork, deployment_id: UUID) -> UUID | None:
    with uow:
        deployment = uow.deployments.find_deployment(deployment_id)
    assert deployment is not None
    return deployment.active_version_id


def _state(uow: InMemoryUnitOfWork, version_id: UUID) -> VersionState:
    with uow:
        version = uow.deployments.find_version(version_id)
    assert version is not None
    return version.state


def test_activation_makes_a_ready_version_the_route_target(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")
    (ready,) = _versions(uow, deployment_id)

    operation = service.activation.activate_version(
        deployment_id,
        ready.id,
        "act-1",
        CORR,
        TEST_PRINCIPAL,
    )

    assert operation.state is OperationState.SUCCEEDED
    assert _state(uow, ready.id) is VersionState.ACTIVE
    assert _active_version_id(uow, deployment_id) == ready.id


def test_replacing_the_active_version_steps_the_previous_one_down(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")
    _deploy(service, deployment_id, package_id, "k2")
    v2, v1 = _versions(uow, deployment_id)  # newest attempt first

    service.activation.activate_version(
        deployment_id, v1.id, "act-1", CORR, TEST_PRINCIPAL
    )
    service.activation.activate_version(
        deployment_id, v2.id, "act-2", CORR, TEST_PRINCIPAL
    )

    assert _state(uow, v2.id) is VersionState.ACTIVE
    assert _state(uow, v1.id) is VersionState.READY  # stepped down, still runnable
    assert _active_version_id(uow, deployment_id) == v2.id

    # Rollback is simply activating the previous version again.
    rollback = service.activation.activate_version(
        deployment_id, v1.id, "act-3", CORR, TEST_PRINCIPAL
    )
    assert rollback.state is OperationState.SUCCEEDED
    assert _state(uow, v1.id) is VersionState.ACTIVE
    assert _state(uow, v2.id) is VersionState.READY
    assert _active_version_id(uow, deployment_id) == v1.id


def test_activation_is_refused_when_the_candidate_is_unhealthy(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")
    (v1,) = _versions(uow, deployment_id)
    service.activation.activate_version(
        deployment_id, v1.id, "act-1", CORR, TEST_PRINCIPAL
    )

    # A second version whose runtime never becomes healthy.
    runtime.healthy = False
    _deploy(service, deployment_id, package_id, "k2")
    v2 = next(v for v in _versions(uow, deployment_id) if v.id != v1.id)

    operation = service.activation.activate_version(
        deployment_id, v2.id, "act-2", CORR, TEST_PRINCIPAL
    )

    assert operation.state is OperationState.FAILED
    assert operation.failure is not None
    assert operation.failure.code == "candidate_not_healthy"
    # The previous active version is untouched; the candidate stays READY.
    assert _active_version_id(uow, deployment_id) == v1.id
    assert _state(uow, v1.id) is VersionState.ACTIVE
    assert _state(uow, v2.id) is VersionState.READY


def test_reactivating_the_active_version_is_idempotent(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")
    (v1,) = _versions(uow, deployment_id)
    service.activation.activate_version(
        deployment_id, v1.id, "act-1", CORR, TEST_PRINCIPAL
    )

    # A distinct key against an already-active version succeeds without change.
    again = service.activation.activate_version(
        deployment_id, v1.id, "act-2", CORR, TEST_PRINCIPAL
    )
    assert again.state is OperationState.SUCCEEDED
    assert _state(uow, v1.id) is VersionState.ACTIVE


def test_activating_a_failed_version_conflicts(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    runtime.build_failure = OperationFailure(code="build_failed", message="x")
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")
    (failed,) = _versions(uow, deployment_id)

    with pytest.raises(AppError) as captured:
        service.activation.activate_version(
            deployment_id, failed.id, "act-1", CORR, TEST_PRINCIPAL
        )
    assert captured.value.category is ErrorCategory.CONFLICT
    assert captured.value.code == "invalid_state_transition"


def test_runtime_unavailable_during_activation_preserves_state(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")
    (v1,) = _versions(uow, deployment_id)

    runtime.available = False
    operation = service.activation.activate_version(
        deployment_id, v1.id, "act-1", CORR, TEST_PRINCIPAL
    )

    assert operation.state is OperationState.FAILED
    assert operation.failure is not None
    assert operation.failure.code == "runtime_unavailable"
    assert _state(uow, v1.id) is VersionState.READY
    assert _active_version_id(uow, deployment_id) is None


def test_stopping_the_active_version_removes_the_route_first(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")
    (v1,) = _versions(uow, deployment_id)
    service.activation.activate_version(
        deployment_id, v1.id, "act-1", CORR, TEST_PRINCIPAL
    )

    service.lifecycle.stop_version(v1.id, "stop-1", CORR, TEST_PRINCIPAL)

    assert _state(uow, v1.id) is VersionState.STOPPED
    assert _active_version_id(uow, deployment_id) is None


def test_activating_an_unknown_version_is_not_found(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    with pytest.raises(AppError) as captured:
        service.activation.activate_version(
            deployment_id, uuid4(), "act-1", CORR, TEST_PRINCIPAL
        )
    assert captured.value.category is ErrorCategory.NOT_FOUND


def test_deploying_an_unknown_package_is_not_found(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    with pytest.raises(AppError) as captured:
        _deploy(service, deployment_id, uuid4(), "k1")
    assert captured.value.category is ErrorCategory.NOT_FOUND
    assert captured.value.code == "package_not_found"


def test_stop_fails_the_operation_when_docker_is_unavailable(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")
    (ready,) = _versions(uow, deployment_id)

    runtime.available = False
    operation = service.lifecycle.stop_version(ready.id, "stop-1", CORR, TEST_PRINCIPAL)
    assert operation.state is OperationState.FAILED
    assert operation.failure is not None
    assert operation.failure.code == "runtime_unavailable"


def test_reconcile_fails_the_operation_when_docker_is_unavailable(
    service: DeploymentServices, runtime: FakeRuntimeManager
) -> None:
    runtime.available = False
    operation = service.reconciliation.reconcile("rec-1", CORR)
    assert operation.state is OperationState.FAILED
    assert operation.failure is not None
    assert operation.failure.code == "runtime_unavailable"


def test_a_replayed_deploy_returns_one_operation_and_one_version(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id

    first = _deploy(service, deployment_id, package_id, "same-key")
    second = _deploy(service, deployment_id, package_id, "same-key")

    assert first.id == second.id
    assert len(_versions(uow, deployment_id)) == 1


def test_docker_unavailable_fails_the_operation_retriably(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    runtime.available = False
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id

    operation = _deploy(service, deployment_id, package_id, "k1")

    assert operation.state is OperationState.FAILED
    assert operation.failure is not None
    assert operation.failure.code == "runtime_unavailable"


def test_reconcile_reports_a_healthy_known_runtime_as_clean(
    service: DeploymentServices, uow: InMemoryUnitOfWork
) -> None:
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")

    operation = service.reconciliation.reconcile("rec-1", CORR)

    assert operation.state is OperationState.SUCCEEDED
    assert operation.result == {"observed": "1", "mismatches": "0"}


def test_reconcile_flags_an_unhealthy_runtime(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    runtime.healthy = False
    package_id = _accept_package(uow)
    deployment_id = service.lifecycle.create_deployment(
        "scorer", CORR, TEST_PRINCIPAL
    ).id
    _deploy(service, deployment_id, package_id, "k1")

    operation = service.reconciliation.reconcile("rec-1", CORR)

    assert operation.result is not None
    assert operation.result["mismatches"] == "1"


def test_reconcile_flags_an_unknown_runtime(
    service: DeploymentServices, uow: InMemoryUnitOfWork, runtime: FakeRuntimeManager
) -> None:
    # A container the runtime reports but the database has never heard of.
    runtime.start(uuid4(), runtime.build(uuid4(), _context(), "a" * 64, POLICY), POLICY)

    operation = service.reconciliation.reconcile("rec-1", CORR)

    assert operation.result is not None
    assert operation.result["mismatches"] == "1"


def _context() -> GeneratedBuildContext:
    return generate(
        analyze(ManifestV1.model_validate(VALID_MANIFEST)), checksum="a" * 64
    )
