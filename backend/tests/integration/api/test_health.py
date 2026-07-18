"""Health endpoint integration tests."""

from uuid import UUID

from fastapi import Request

from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings
from tests.support import ASGITestClient, stub_application


def test_liveness_reports_the_process_is_up(settings: AppSettings) -> None:
    client = ASGITestClient(create_application(settings))

    health = client.get("/healthz")

    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "service": "forgeml-control-plane",
        "version": "0.1.0",
    }
    assert health.headers["content-type"] == "application/json"
    assert UUID(health.headers["x-request-id"]).version == 4


def test_readiness_fails_closed_without_a_metadata_database(
    settings: AppSettings,
) -> None:
    # Since Module 2 the control plane cannot serve without its database.
    # Readiness that answered "ready" here would route traffic at a process that
    # cannot honour a single request.
    client = ASGITestClient(create_application(settings))

    ready = client.get("/readyz")

    assert ready.status_code == 503
    assert ready.json()["code"] == "dependency_unavailable"
    assert UUID(ready.headers["x-request-id"]).version == 4


def test_inbound_request_ids_are_ignored(settings: AppSettings) -> None:
    app, token = stub_application(settings)

    @app.get("/test/request-id")
    async def request_id_header(request: Request) -> dict[str, str | None]:
        return {"seen": request.headers.get("x-request-id")}

    client = ASGITestClient(app, credential=token)

    response = client.get(
        "/test/request-id",
        headers=[
            ("X-Request-ID", "client-one"),
            ("X-Request-ID", "client-two"),
        ],
    )

    server_id = response.headers["x-request-id"]
    assert server_id not in {"client-one", "client-two"}
    assert UUID(server_id).version == 4
    assert response.json() == {"seen": None}


def test_docs_and_openapi_routes_are_not_public(settings: AppSettings) -> None:
    """Epic 1 made this stricter: these answer 401, not 404.

    Authentication runs before routing (ADR-025), so an unauthenticated caller
    cannot tell an absent route from a protected one. That is the stronger
    property -- 404 would have confirmed which paths exist, which is how route
    enumeration starts. `/v1/openapi.json` is authenticated rather than absent,
    per ADR-019.
    """

    client = ASGITestClient(create_application(settings))

    for path in ("/docs", "/redoc", "/openapi.json", "/v1/openapi.json"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.json()["code"] == "authentication_required"
        assert response.headers["WWW-Authenticate"] == "Bearer"
