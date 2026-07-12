"""Frozen HTTP wire contract tests."""

from uuid import UUID

from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings
from tests.support import ASGITestClient


def test_health_wire_shapes_and_header(settings: AppSettings) -> None:
    client = ASGITestClient(create_application(settings))

    cases = {"/healthz": "ok", "/readyz": "ready"}
    for path, status in cases.items():
        response = client.get(path)
        assert set(response.json()) == {"status", "service", "version"}
        assert response.json()["status"] == status
        assert response.headers["content-type"] == "application/json"
        assert UUID(response.headers["x-request-id"]).version == 4


def test_framework_error_wire_shape_omits_empty_details(settings: AppSettings) -> None:
    response = ASGITestClient(create_application(settings)).get("/missing")

    assert set(response.json()) == {"code", "message", "request_id"}
    assert response.json() == {
        "code": "route_not_found",
        "message": "Resource not found.",
        "request_id": response.headers["x-request-id"],
    }
