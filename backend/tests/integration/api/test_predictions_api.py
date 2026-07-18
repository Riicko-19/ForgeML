"""HTTP contract for the platform prediction route (docs 12).

Drives POST /v1/deployments/{name}/predict end to end against the in-memory unit
of work, the fake runtime, and a fake gateway, asserting status codes and the
error envelope. The client addresses a deployment by name and never sees a
container or an endpoint.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from forgeml.api.error_handlers import register_error_handlers
from forgeml.api.middleware import RequestContextMiddleware
from forgeml.api.v1.deployments import create_deployment_router
from forgeml.api.v1.predictions import create_prediction_router
from forgeml.application.deployment.services import DeploymentServices
from forgeml.application.routing.services import RouteManager
from forgeml.domain.deployment.models import ResourcePolicy
from forgeml.domain.package.analyzer import analyze
from forgeml.domain.package.models import (
    ManifestV1,
    PackageValidation,
    ValidationState,
)
from forgeml.domain.routing.ports import PredictionUpstreamError
from tests.fake_runtime import FakeRuntimeManager
from tests.fakes import InMemoryUnitOfWork
from tests.packages import VALID_MANIFEST
from tests.support import TEST_PRINCIPAL, ASGITestClient, authenticate


class FakeGateway:
    def __init__(self) -> None:
        self.response: Any = {"result": {"score": 9.0}}
        self.error: Exception | None = None

    def predict(self, endpoint: str, payload: Any) -> Any:
        if self.error is not None:
            raise self.error
        return self.response


@pytest.fixture
def env() -> SimpleNamespace:
    uow = InMemoryUnitOfWork()
    runtime = FakeRuntimeManager()
    gateway = FakeGateway()
    deployments = DeploymentServices.create(lambda: uow, runtime)
    routing = RouteManager(deployments.queries, runtime, gateway)

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(create_deployment_router(deployments), prefix="/v1")
    app.include_router(create_prediction_router(routing), prefix="/v1")
    token = authenticate(app, uow)
    app.add_middleware(RequestContextMiddleware)
    return SimpleNamespace(
        client=ASGITestClient(app, credential=token),
        uow=uow,
        deployments=deployments,
        gateway=gateway,
    )


def _predict(client: ASGITestClient, name: str, payload: Any) -> httpx.Response:
    return client.request(
        "POST",
        f"/v1/deployments/{name}/predict",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload).encode(),
    )


def _activate_deployment(env: SimpleNamespace, name: str = "scorer") -> None:
    manifest = ManifestV1.model_validate(VALID_MANIFEST)
    with env.uow:
        package = env.uow.packages.get_or_create(
            "a" * 64, "m.forge", 10, "artifact://a"
        )
        env.uow.packages.save_validation(
            package.id,
            PackageValidation(
                state=ValidationState.VALIDATED,
                validator_version="1",
                findings=(),
                manifest=manifest,
                contract=analyze(manifest),
            ),
        )
        env.uow.commit()
    deployment = env.deployments.lifecycle.create_deployment(
        name, uuid4(), TEST_PRINCIPAL
    )
    env.deployments.lifecycle.deploy_version(
        deployment.id,
        package.id,
        ResourcePolicy(),
        "d1",
        uuid4(),
        TEST_PRINCIPAL,
    )
    with env.uow:
        (version,) = env.uow.deployments.list_versions(deployment.id)
    env.deployments.activation.activate_version(
        deployment.id,
        version.id,
        "a1",
        uuid4(),
        TEST_PRINCIPAL,
    )


def test_prediction_returns_the_model_output(env: SimpleNamespace) -> None:
    _activate_deployment(env)
    response = _predict(env.client, "scorer", {"value": 21.0})
    assert response.status_code == 200
    assert response.json() == {"score": 9.0}


def test_no_active_version_is_503(env: SimpleNamespace) -> None:
    response = _predict(env.client, "scorer", {"value": 1.0})
    assert response.status_code == 503
    assert response.json()["code"] == "deployment_unavailable"


def test_invalid_input_is_422(env: SimpleNamespace) -> None:
    _activate_deployment(env)
    response = _predict(env.client, "scorer", {"wrong": 1})
    assert response.status_code == 422
    assert response.json()["code"] == "prediction_input_invalid"


def test_runtime_failure_is_502(env: SimpleNamespace) -> None:
    _activate_deployment(env)
    env.gateway.error = PredictionUpstreamError("model crashed")
    response = _predict(env.client, "scorer", {"value": 1.0})
    assert response.status_code == 502
    assert response.json()["code"] == "prediction_runtime_failed"
    # The model's own error never reaches the client.
    assert "crashed" not in response.text
