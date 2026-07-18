"""The authentication boundary over HTTP (ADR-025).

These are the tests that hold the guarantee. If one of them starts failing, a
route has become reachable without a credential.
"""

from __future__ import annotations

import pytest
from fastapi.routing import APIRoute

from forgeml.api.authentication import PUBLIC_PATHS
from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings
from tests.support import ASGITestClient, stub_application

UNAUTHENTICATED_CODE = "authentication_required"


def _routes(app: object) -> list[tuple[str, str]]:
    """Every concrete route the application serves, with one usable method."""

    found: list[tuple[str, str]] = []
    for route in app.routes:  # type: ignore[attr-defined]
        if not isinstance(route, APIRoute):
            continue
        if "{" in route.path:
            continue  # parameterised paths are covered by the API test suites
        methods = route.methods or set()
        method = next(iter(sorted(methods - {"HEAD", "OPTIONS"})), None)
        if method is not None:
            found.append((method, route.path))
    return found


def test_every_route_that_is_not_public_refuses_an_anonymous_caller(
    settings: AppSettings,
) -> None:
    """The guarantee, enumerated from the app rather than from a list.

    Reading the routes off the application means a route added tomorrow is
    covered by this test today. A hand-maintained list would drift, and the
    drift would be silent and in the unsafe direction.
    """

    app = create_application(settings)

    for method, path in _routes(app):
        response = ASGITestClient(app).request(method, path)
        if path in PUBLIC_PATHS:
            assert response.status_code != 401, f"{path} should be public"
            continue
        assert response.status_code == 401, f"{method} {path} did not require auth"
        assert response.json()["code"] == UNAUTHENTICATED_CODE


def test_the_public_list_is_exactly_the_two_documented_paths() -> None:
    """ADR-025 closed this list. Widening it is a decision, not an edit.

    This test exists to make adding a public route require deleting an
    assertion -- a moment loud enough to notice in review.
    """

    assert frozenset({"/healthz", "/readyz"}) == PUBLIC_PATHS


def test_health_and_readiness_need_no_credential(settings: AppSettings) -> None:
    client = ASGITestClient(create_application(settings))

    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code in {200, 503}


def test_a_valid_credential_is_admitted(settings: AppSettings) -> None:
    app, token = stub_application(settings)

    response = ASGITestClient(app, credential=token).get("/v1/deployments")

    assert response.status_code != 401


@pytest.mark.parametrize(
    "header",
    [
        "",
        "Bearer",
        "Bearer ",
        "forge_token_without_scheme",
        "Basic dXNlcjpwYXNz",
        "Bearer forge_short_x",
        "Digest something",
        "Bearer  ",
    ],
)
def test_a_malformed_authorization_header_is_refused(
    settings: AppSettings, header: str
) -> None:
    app, _ = stub_application(settings)

    response = ASGITestClient(app).get(
        "/v1/deployments", headers={"Authorization": header}
    )

    assert response.status_code == 401
    assert response.json()["code"] == UNAUTHENTICATED_CODE


def test_the_bearer_scheme_is_case_insensitive(settings: AppSettings) -> None:
    """RFC 7235 says the scheme is case-insensitive; a client sending `bearer`
    is not wrong, and refusing it would be a bug that looks like security."""

    app, token = stub_application(settings)
    client = ASGITestClient(app)

    for scheme in ("Bearer", "bearer", "BEARER", "BeArEr"):
        response = client.get(
            "/v1/deployments", headers={"Authorization": f"{scheme} {token}"}
        )
        assert response.status_code != 401, scheme


@pytest.mark.parametrize(
    "raw",
    [
        b"Bearer \xff\xfe",  # not decodable as ASCII
        b"\xc3\x28",  # invalid UTF-8 too
        b"Bearer \x00\x01",
    ],
)
def test_undecodable_header_bytes_are_refused_not_crashed(raw: bytes) -> None:
    """Header bytes are attacker-controlled and need not be text at all.

    Driven at the parser rather than through the client, because httpx refuses
    to *send* a non-ASCII header -- but a hand-written client, or anything
    speaking raw HTTP, has no such scruples. A decode error here would surface
    as a 500 and, worse, as an unhandled exception on the auth path.
    """

    from forgeml.api.authentication import _presented_token

    scope = {"type": "http", "headers": [(b"authorization", raw)]}

    assert _presented_token(scope) is None


def test_the_401_carries_www_authenticate_and_no_detail(
    settings: AppSettings,
) -> None:
    """RFC 7235 requires the header. The body says nothing about why."""

    response = ASGITestClient(create_application(settings)).get("/v1/deployments")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert set(response.json()) == {"code", "message", "request_id"}
    assert "realm" not in response.headers["WWW-Authenticate"]


def test_an_unauthenticated_response_still_carries_a_request_id(
    settings: AppSettings,
) -> None:
    """Request context wraps authentication, so a 401 is traceable like anything
    else. An untraceable rejection is one nobody can debug during an incident."""

    response = ASGITestClient(create_application(settings)).get("/v1/deployments")

    assert response.headers["x-request-id"]
    assert response.json()["request_id"] == response.headers["x-request-id"]


def test_the_credential_is_not_echoed_in_any_error(settings: AppSettings) -> None:
    app, _ = stub_application(settings)
    secret = "forge_" + "a" * 16 + "_super-secret-value"

    response = ASGITestClient(app).get(
        "/v1/deployments", headers={"Authorization": f"Bearer {secret}"}
    )

    assert "super-secret-value" not in response.text
    assert secret not in response.text


def test_there_is_no_setting_that_disables_authentication() -> None:
    """ADR-025, asserted structurally.

    The control plane drives a root daemon, so a bypass here would be a root
    bypass. This checks that no configuration field has appeared that could
    become one.
    """

    from forgeml.core.config import AppSettings as Settings

    suspicious = {
        name
        for name in Settings.model_fields
        if any(word in name.lower() for word in ("auth", "secure", "insecure"))
    }

    assert suspicious == set()
