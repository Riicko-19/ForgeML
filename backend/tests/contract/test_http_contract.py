"""Frozen HTTP wire contract tests."""

from uuid import UUID

from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings
from tests.support import ASGITestClient, stub_application


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
    """The envelope shape holds for a framework error, reached authenticated.

    Epic 1 put authentication in front of routing, so an unknown path answers
    401 to an anonymous caller. The wire shape under test is the same either
    way, and `test_unauthenticated_wire_shape_omits_empty_details` covers the
    401 form.
    """

    app, token = stub_application(settings)
    response = ASGITestClient(app, credential=token).get("/missing")

    assert set(response.json()) == {"code", "message", "request_id"}
    assert response.json() == {
        "code": "route_not_found",
        "message": "Resource not found.",
        "request_id": response.headers["x-request-id"],
    }


def test_unauthenticated_wire_shape_omits_empty_details(
    settings: AppSettings,
) -> None:
    """A 401 is the frozen envelope too, and carries WWW-Authenticate."""

    response = ASGITestClient(create_application(settings)).get("/v1/deployments")

    assert set(response.json()) == {"code", "message", "request_id"}
    assert response.json() == {
        "code": "authentication_required",
        "message": "a valid api key is required",
        "request_id": response.headers["x-request-id"],
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"
