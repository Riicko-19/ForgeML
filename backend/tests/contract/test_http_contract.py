"""Frozen HTTP wire contract tests."""

from uuid import UUID

from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings
from tests.support import ASGITestClient


def test_health_wire_shapes_and_header(settings: AppSettings) -> None:
    client = ASGITestClient(create_application(settings))

    response = client.get("/healthz")

    assert set(response.json()) == {"status", "service", "version"}
    assert response.json()["status"] == "ok"
    assert response.headers["content-type"] == "application/json"
    assert UUID(response.headers["x-request-id"]).version == 4


def test_unavailable_readiness_uses_the_frozen_error_envelope(
    settings: AppSettings,
) -> None:
    # No database is configured here, so readiness must fail closed -- and it
    # must do so in the same envelope as every other error.
    response = ASGITestClient(create_application(settings)).get("/readyz")

    assert response.status_code == 503
    assert set(response.json()) == {"code", "message", "request_id"}
    assert response.json()["code"] == "dependency_unavailable"


def test_framework_error_wire_shape_omits_empty_details(settings: AppSettings) -> None:
    response = ASGITestClient(create_application(settings)).get("/missing")

    assert set(response.json()) == {"code", "message", "request_id"}
    assert response.json() == {
        "code": "route_not_found",
        "message": "Resource not found.",
        "request_id": response.headers["x-request-id"],
    }
