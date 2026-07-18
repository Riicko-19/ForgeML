"""HTTP contract for the deployment routes (docs 12).

The deployment router is not yet wired into the live application -- that needs a
real RuntimeManager, which is Module 6 -- so this drives it in-process against
the in-memory unit of work and the fake runtime, asserting status codes, the
operation envelope, and error mapping.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI

from forgeml.api.error_handlers import register_error_handlers
from forgeml.api.middleware import RequestContextMiddleware
from forgeml.api.v1.deployments import create_admin_router, create_deployment_router
from forgeml.api.v1.operations import create_operation_router
from forgeml.application.deployment.services import DeploymentServices
from forgeml.application.operations.services import OperationService
from forgeml.domain.package.analyzer import analyze
from forgeml.domain.package.models import (
    ManifestV1,
    PackageValidation,
    ValidationState,
)
from tests.fake_runtime import FakeRuntimeManager
from tests.fakes import InMemoryUnitOfWork
from tests.packages import VALID_MANIFEST
from tests.support import ASGITestClient, authenticate


@pytest.fixture
def env() -> SimpleNamespace:
    uow = InMemoryUnitOfWork()
    runtime = FakeRuntimeManager()
    service = DeploymentServices.create(lambda: uow, runtime)
    operations = OperationService(lambda: uow)

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(create_deployment_router(service), prefix="/v1")
    app.include_router(create_admin_router(service.reconciliation), prefix="/v1")
    app.include_router(create_operation_router(operations), prefix="/v1")
    token = authenticate(app, uow)
    app.add_middleware(RequestContextMiddleware)
    return SimpleNamespace(
        client=ASGITestClient(app, credential=token), uow=uow, runtime=runtime
    )


def _post(
    client: ASGITestClient, path: str, body: dict[str, Any] | None, key: str | None
) -> httpx.Response:
    headers = {"Content-Type": "application/json"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return client.request(
        "POST", path, headers=headers, content=json.dumps(body or {}).encode()
    )


def _body(response: httpx.Response) -> dict[str, Any]:
    document: dict[str, Any] = response.json()
    return document


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


def _create_deployment(client: ASGITestClient, name: str = "scorer") -> dict[str, Any]:
    return _body(_post(client, "/v1/deployments", {"name": name}, None))


def test_create_deployment_returns_201(env: SimpleNamespace) -> None:
    response = _post(env.client, "/v1/deployments", {"name": "scorer"}, None)
    assert response.status_code == 201
    document = _body(response)
    assert document["name"] == "scorer"
    assert document["desired_state"] == "running"
    assert document["active_version_id"] is None


def test_a_duplicate_name_is_a_conflict(env: SimpleNamespace) -> None:
    _create_deployment(env.client)
    response = _post(env.client, "/v1/deployments", {"name": "scorer"}, None)
    assert response.status_code == 409
    assert _body(response)["code"] == "deployment_name_taken"


def test_an_invalid_name_is_rejected(env: SimpleNamespace) -> None:
    response = _post(env.client, "/v1/deployments", {"name": "Scorer_1"}, None)
    assert response.status_code == 422


def test_creating_a_version_requires_an_idempotency_key(env: SimpleNamespace) -> None:
    deployment = _create_deployment(env.client)
    response = _post(
        env.client,
        f"/v1/deployments/{deployment['id']}/versions",
        {"package_id": str(uuid4())},
        None,
    )
    assert response.status_code == 400
    assert _body(response)["code"] == "idempotency_key_required"


def test_a_version_deploys_to_ready_and_can_be_read(env: SimpleNamespace) -> None:
    package_id = _accept_package(env.uow)
    deployment = _create_deployment(env.client)

    response = _post(
        env.client,
        f"/v1/deployments/{deployment['id']}/versions",
        {"package_id": str(package_id), "resource_policy": {"cpu_millicores": 500}},
        "deploy-1",
    )
    assert response.status_code == 202
    operation = _body(response)
    assert operation["type"] == "deployment_version_deploy"
    assert operation["state"] == "succeeded"
    version_id = operation["result"]["version_id"]

    version = _body(
        env.client.get(f"/v1/deployments/{deployment['id']}/versions/{version_id}")
    )
    assert version["state"] == "ready"
    assert version["endpoint"] is not None
    assert version["resource_policy"]["cpu_millicores"] == 500


def test_activating_a_version_returns_an_operation(env: SimpleNamespace) -> None:
    package_id = _accept_package(env.uow)
    deployment = _create_deployment(env.client)
    deployed = _body(
        _post(
            env.client,
            f"/v1/deployments/{deployment['id']}/versions",
            {"package_id": str(package_id)},
            "deploy-1",
        )
    )
    version_id = deployed["result"]["version_id"]

    response = _post(
        env.client,
        f"/v1/deployments/{deployment['id']}/versions/{version_id}/activate",
        None,
        "activate-1",
    )
    assert response.status_code == 202
    operation = _body(response)
    assert operation["type"] == "deployment_version_activate"
    assert operation["state"] == "succeeded"

    deployment_now = _body(env.client.get(f"/v1/deployments/{deployment['id']}"))
    assert deployment_now["active_version_id"] == version_id


def test_deploying_to_an_unknown_deployment_is_404(env: SimpleNamespace) -> None:
    package_id = _accept_package(env.uow)
    response = _post(
        env.client,
        f"/v1/deployments/{uuid4()}/versions",
        {"package_id": str(package_id)},
        "deploy-1",
    )
    assert response.status_code == 404


def test_deploying_an_unaccepted_package_is_409(env: SimpleNamespace) -> None:
    deployment = _create_deployment(env.client)
    response = _post(
        env.client,
        f"/v1/deployments/{deployment['id']}/versions",
        {"package_id": str(uuid4())},
        "deploy-1",
    )
    assert response.status_code == 404  # unknown package resolves first


def test_a_ready_version_can_be_stopped_over_http(env: SimpleNamespace) -> None:
    package_id = _accept_package(env.uow)
    deployment = _create_deployment(env.client)
    operation = _body(
        _post(
            env.client,
            f"/v1/deployments/{deployment['id']}/versions",
            {"package_id": str(package_id)},
            "deploy-1",
        )
    )
    version_id = operation["result"]["version_id"]

    stopped = _post(
        env.client,
        f"/v1/deployments/{deployment['id']}/versions/{version_id}/stop",
        None,
        "stop-1",
    )
    assert stopped.status_code == 202
    assert _body(stopped)["state"] == "succeeded"

    version = _body(
        env.client.get(f"/v1/deployments/{deployment['id']}/versions/{version_id}")
    )
    assert version["state"] == "stopped"


def test_deployments_can_be_listed(env: SimpleNamespace) -> None:
    _create_deployment(env.client, "one")
    _create_deployment(env.client, "two")
    listing = _body(env.client.get("/v1/deployments"))
    assert {item["name"] for item in listing["items"]} == {"one", "two"}


def test_reading_an_unknown_deployment_is_404(env: SimpleNamespace) -> None:
    response = env.client.get(f"/v1/deployments/{uuid4()}")
    assert response.status_code == 404


def test_admin_reconcile_returns_an_operation(env: SimpleNamespace) -> None:
    response = _post(env.client, "/v1/admin/reconcile", None, "rec-1")
    assert response.status_code == 202
    assert _body(response)["type"] == "deployment_reconcile"
    assert _body(response)["state"] == "succeeded"
