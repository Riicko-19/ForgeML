"""Health endpoint integration tests."""

from uuid import UUID

from fastapi import Request

from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings
from tests.support import ASGITestClient


def test_health_and_readiness_contract(settings: AppSettings) -> None:
    client = ASGITestClient(create_application(settings))

    health = client.get("/healthz")
    ready = client.get("/readyz")

    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "service": "forgeml-control-plane",
        "version": "0.1.0",
    }
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert health.headers["content-type"] == "application/json"
    assert UUID(health.headers["x-request-id"]).version == 4
    assert UUID(ready.headers["x-request-id"]).version == 4


def test_inbound_request_ids_are_ignored(settings: AppSettings) -> None:
    app = create_application(settings)

    @app.get("/test/request-id")
    async def request_id_header(request: Request) -> dict[str, str | None]:
        return {"seen": request.headers.get("x-request-id")}

    client = ASGITestClient(app)

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
    client = ASGITestClient(create_application(settings))

    for path in ("/docs", "/redoc", "/openapi.json"):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json()["code"] == "route_not_found"
