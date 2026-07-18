"""RouteManager: active-version resolution, health gating, and proxying.

Drives a deployment to an ACTIVE version against the in-memory unit of work and
the fake runtime, then exercises prediction success and every failure the
platform must map (docs 12): 422 bad input, 503 no active healthy runtime, 502
runtime failure. The prediction gateway is a fake, so no HTTP or Docker is
involved; the real HTTP gateway is covered separately.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

import pytest

from forgeml.application.deployment.services import DeploymentService
from forgeml.application.routing.services import RouteManager
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.deployment.models import ResourcePolicy
from forgeml.domain.package.analyzer import analyze
from forgeml.domain.package.models import (
    ManifestV1,
    PackageValidation,
    ValidationState,
)
from forgeml.domain.routing.ports import (
    PredictionUnavailable,
    PredictionUpstreamError,
)
from tests.fake_runtime import FakeRuntimeManager
from tests.fakes import InMemoryUnitOfWork
from tests.packages import VALID_MANIFEST

CORR = uuid4()
POLICY = ResourcePolicy(cpu_millicores=500, memory_mib=256)


class FakeGateway:
    """A scriptable prediction gateway."""

    def __init__(self) -> None:
        self.response: Any = {"result": {"score": 2.0}}
        self.error: Exception | None = None
        self.calls: list[tuple[str, Any]] = []

    def predict(self, endpoint: str, payload: Any) -> Any:
        self.calls.append((endpoint, payload))
        if self.error is not None:
            raise self.error
        return self.response


def _accept_package(uow: InMemoryUnitOfWork) -> UUID:
    manifest = ManifestV1.model_validate(VALID_MANIFEST)
    with uow:
        package = uow.packages.get_or_create("a" * 64, "m.forge", 10, "artifact://a")
        uow.packages.save_validation(
            package.id,
            PackageValidation(
                state=ValidationState.VALIDATED,
                validator_version="1",
                findings=(),
                manifest=manifest,
                contract=analyze(manifest),
            ),
        )
        uow.commit()
    return package.id


@pytest.fixture
def env() -> tuple[
    RouteManager,
    DeploymentService,
    InMemoryUnitOfWork,
    FakeRuntimeManager,
    FakeGateway,
]:
    uow = InMemoryUnitOfWork()
    runtime = FakeRuntimeManager()
    gateway = FakeGateway()
    deployments = DeploymentService(lambda: uow, runtime)
    routing = RouteManager(deployments, runtime, gateway)
    return routing, deployments, uow, runtime, gateway


def _active_deployment(deployments: DeploymentService, uow: InMemoryUnitOfWork) -> str:
    package_id = _accept_package(uow)
    deployment = deployments.create_deployment("scorer", CORR)
    deployments.deploy_version(deployment.id, package_id, POLICY, "d1", CORR)
    with uow:
        (version,) = uow.deployments.list_versions(deployment.id)
    deployments.activate_version(deployment.id, version.id, "a1", CORR)
    return deployment.name


def test_prediction_reaches_the_active_runtime(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, deployments, uow, _runtime, gateway = env
    name = _active_deployment(deployments, uow)

    result = routing.predict(name, {"value": 21.0}, CORR)

    assert result == {"score": 2.0}
    # The client's payload was forwarded to the resolved internal endpoint.
    assert gateway.calls[0][1] == {"value": 21.0}
    assert gateway.calls[0][0].startswith("http://")


def test_no_active_version_is_unavailable(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, deployments, uow, _runtime, _gateway = env
    package_id = _accept_package(uow)
    deployment = deployments.create_deployment("scorer", CORR)
    deployments.deploy_version(deployment.id, package_id, POLICY, "d1", CORR)
    # Deployed but never activated: nothing to route to.

    with pytest.raises(AppError) as caught:
        routing.predict("scorer", {"value": 1.0}, CORR)
    assert caught.value.category is ErrorCategory.DEPENDENCY_UNAVAILABLE
    assert caught.value.code == "deployment_unavailable"


def test_unknown_deployment_is_unavailable(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, *_ = env
    with pytest.raises(AppError) as caught:
        routing.predict("ghost", {"value": 1.0}, CORR)
    assert caught.value.code == "deployment_unavailable"


def test_invalid_input_is_rejected_before_forwarding(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, deployments, uow, _runtime, gateway = env
    name = _active_deployment(deployments, uow)

    with pytest.raises(AppError) as caught:
        routing.predict(name, {"wrong": 1}, CORR)  # missing required "value"
    assert caught.value.category is ErrorCategory.VALIDATION
    assert caught.value.code == "prediction_input_invalid"
    assert gateway.calls == []  # never forwarded


def test_unhealthy_runtime_is_unavailable(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, deployments, uow, runtime, _gateway = env
    name = _active_deployment(deployments, uow)
    with uow:
        (version,) = uow.deployments.list_versions(
            uow.deployments.find_deployment_by_name(name).id  # type: ignore[union-attr]
        )
    assert version.container_id is not None
    managed = runtime._containers[version.container_id]
    runtime._containers[version.container_id] = replace(
        managed, status=replace(managed.status, healthy=False)
    )

    with pytest.raises(AppError) as caught:
        routing.predict(name, {"value": 1.0}, CORR)
    assert caught.value.code == "deployment_unavailable"


def test_runtime_unavailable_is_unavailable(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, deployments, uow, runtime, _gateway = env
    name = _active_deployment(deployments, uow)
    runtime.available = False

    with pytest.raises(AppError) as caught:
        routing.predict(name, {"value": 1.0}, CORR)
    assert caught.value.code == "deployment_unavailable"


def test_unreachable_runtime_maps_to_unavailable(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, deployments, uow, _runtime, gateway = env
    name = _active_deployment(deployments, uow)
    gateway.error = PredictionUnavailable("connection refused")

    with pytest.raises(AppError) as caught:
        routing.predict(name, {"value": 1.0}, CORR)
    assert caught.value.code == "deployment_unavailable"


def test_runtime_error_maps_to_prediction_runtime_failed(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, deployments, uow, _runtime, gateway = env
    name = _active_deployment(deployments, uow)
    gateway.error = PredictionUpstreamError("model crashed")

    with pytest.raises(AppError) as caught:
        routing.predict(name, {"value": 1.0}, CORR)
    assert caught.value.category is ErrorCategory.UPSTREAM_FAILURE
    assert caught.value.code == "prediction_runtime_failed"


def test_output_that_violates_the_schema_is_a_runtime_failure(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, deployments, uow, _runtime, gateway = env
    name = _active_deployment(deployments, uow)
    gateway.response = {"result": {"not_a_score": True}}

    with pytest.raises(AppError) as caught:
        routing.predict(name, {"value": 1.0}, CORR)
    assert caught.value.code == "prediction_runtime_failed"


def test_missing_result_envelope_is_a_runtime_failure(
    env: tuple[
        RouteManager,
        DeploymentService,
        InMemoryUnitOfWork,
        FakeRuntimeManager,
        FakeGateway,
    ],
) -> None:
    routing, deployments, uow, _runtime, gateway = env
    name = _active_deployment(deployments, uow)
    gateway.response = {"error": "prediction_failed"}

    with pytest.raises(AppError) as caught:
        routing.predict(name, {"value": 1.0}, CORR)
    assert caught.value.code == "prediction_runtime_failed"
