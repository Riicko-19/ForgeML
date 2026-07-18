"""HTTP error normalization tests."""

from typing import Annotated

import pytest
from fastapi import Body
from pydantic import BaseModel, ConfigDict

from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings
from forgeml.core.errors import AppError, ErrorCategory, ErrorDetail
from tests.support import ASGITestClient, stub_application


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


def _client_with_failure_routes(settings: AppSettings) -> ASGITestClient:
    app, token = stub_application(settings)

    @app.get("/test/app-error")
    async def app_error() -> None:
        raise AppError(
            category=ErrorCategory.CONFLICT,
            code="state_conflict",
            message="State conflicts with request.",
            details=(
                ErrorDetail(
                    code="field_conflict",
                    message="Field conflicts.",
                    path=("name",),
                ),
            ),
        )

    @app.get("/test/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("secret /host/path")

    @app.post("/test/body")
    async def body(payload: Annotated[Payload, Body()]) -> Payload:
        return payload

    # These probe routes sit outside the public list, so they authenticate like
    # any other -- which is the property ADR-025 wanted: a route added without
    # thinking about auth is protected, not exposed.
    return ASGITestClient(app, credential=token)


def test_404_and_405_use_frozen_envelope(settings: AppSettings) -> None:
    """The frozen envelope still holds, now reached through an authenticated call.

    An unknown path answers 404 only to a caller who authenticated. Without a
    credential it answers 401 (see `test_an_unknown_path_is_401_before_it_is_404`),
    because authentication runs before routing.

    `/healthz` is on the public list, so its 405 needs no credential -- which is
    the point of keeping that list closed and tiny.
    """

    app, token = stub_application(settings)
    client = ASGITestClient(app, credential=token)

    not_found = client.get("/missing")
    wrong_method = client.post("/healthz")

    assert not_found.status_code == 404
    assert not_found.json()["code"] == "route_not_found"
    assert wrong_method.status_code == 405
    assert wrong_method.json()["code"] == "method_not_allowed"
    assert not_found.json()["request_id"] == not_found.headers["x-request-id"]
    assert wrong_method.json()["request_id"] == wrong_method.headers["x-request-id"]


def test_an_unknown_path_is_401_before_it_is_404(settings: AppSettings) -> None:
    """Route existence is not observable without a credential.

    A 404 here would confirm which paths exist, and enumerating the surface is
    the first step of attacking it.
    """

    response = ASGITestClient(create_application(settings)).get("/missing")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"


def test_expected_application_error_is_mapped(settings: AppSettings) -> None:
    response = _client_with_failure_routes(settings).get("/test/app-error")

    assert response.status_code == 409
    assert response.json()["code"] == "state_conflict"
    assert response.json()["details"] == [
        {
            "code": "field_conflict",
            "message": "Field conflicts.",
            "path": ["name"],
        }
    ]


def test_unexpected_error_is_opaque(
    settings: AppSettings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    response = _client_with_failure_routes(settings).get("/test/unexpected")

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    serialized = str(response.json()) + caplog.text
    assert "secret" not in serialized
    assert "/host/path" not in serialized
    assert "Traceback" not in serialized


@pytest.mark.parametrize(
    ("body", "content_type", "status", "code"),
    [
        ('{"name":', "application/json", 400, "request_malformed"),
        ('{"unknown":"x"}', "application/json", 422, "request_validation_failed"),
    ],
)
def test_request_validation_is_sanitized(
    settings: AppSettings,
    body: str,
    content_type: str,
    status: int,
    code: str,
) -> None:
    response = _client_with_failure_routes(settings).post(
        "/test/body",
        content=body,
        headers={"content-type": content_type},
    )

    assert response.status_code == status
    assert response.json()["code"] == code
    assert body not in str(response.json())
