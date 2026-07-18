"""The authentication boundary (ADR-019, ADR-025).

This module is where a credential stops. It reads a header, hands the presented
string to a `CredentialVerifier`, and binds the resulting `Principal` for the
request. No header, token, or request object crosses into `forgeml.application`
-- the services below receive a `Principal`, which is a domain value, exactly as
they already receive a correlation id.

**There is no bypass.** No setting, environment, or header disables this. The
control plane drives the Docker daemon and the daemon is root (ADR-019), so a
development-mode switch here would be a root bypass switch. The exemption list
is two paths, it is a constant in this file rather than configuration, and a
test asserts every other route rejects an unauthenticated request.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from forgeml.api.error_handlers import error_response
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.core.principal import (
    current_authentication,
    reset_authentication,
    set_authentication,
)
from forgeml.domain.identity.models import Principal
from forgeml.domain.identity.ports import CredentialVerifier

#: The closed set of unauthenticated paths (ADR-025). Process supervisors and
#: load balancers hold no credential, and these expose nothing beyond liveness
#: and database reachability. Adding to this list means editing the test that
#: guards it, which is the point: a new route is authenticated by default.
PUBLIC_PATHS: frozenset[str] = frozenset({"/healthz", "/readyz"})

_SCHEME = "bearer"


def authentication_required() -> AppError:
    """The single failure every rejected credential produces.

    Missing, malformed, unknown, wrong, expired, and revoked all map here.
    Telling the client which one applied is an enumeration oracle; the operator
    who needs the real reason has the logs and the CLI (ADR-025).
    """

    return AppError(
        category=ErrorCategory.UNAUTHENTICATED,
        code="authentication_required",
        message="a valid api key is required",
    )


def _presented_token(scope: Scope) -> str | None:
    """Extract a bearer credential from the request headers.

    Case-insensitive on both the header name and the scheme, because RFC 7235
    says so and a client that sends `bearer` is not wrong.
    """

    for name, value in scope.get("headers", []):
        if name.lower() != b"authorization":
            continue
        try:
            raw = value.decode("ascii")
        except UnicodeDecodeError:
            return None
        scheme, _, credential = raw.partition(" ")
        token = credential.strip()
        if scheme.lower() != _SCHEME or not token:
            return None
        # Control characters decode as valid ASCII but are never part of a
        # credential. Rejecting them here keeps them out of the verifier, the
        # store query, and anything downstream that might render them.
        if any(character < " " or character == "\x7f" for character in token):
            return None
        return str(token)
    return None


class AuthenticationMiddleware:
    """Authenticate every request that is not on the public list."""

    def __init__(self, app: ASGIApp, verifier: CredentialVerifier) -> None:
        self._app = app
        self._verifier = verifier

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") in PUBLIC_PATHS:
            await self._app(scope, receive, send)
            return

        token = _presented_token(scope)
        context = self._verifier.verify(token) if token is not None else None
        if context is None:
            await self._unauthenticated()(scope, receive, send)
            return

        authentication = set_authentication(context)
        try:
            await self._app(scope, receive, send)
        finally:
            reset_authentication(authentication)

    @staticmethod
    def _unauthenticated() -> JSONResponse:
        failure = authentication_required()
        response = error_response(
            status_code=401,
            code=failure.code,
            message=failure.message,
        )
        # RFC 7235 requires this on a 401, and it tells a correct client what to
        # present. It names the scheme and nothing else -- no realm, no error
        # detail, nothing that distinguishes why the credential was refused.
        response.headers["WWW-Authenticate"] = "Bearer"
        return response


def current_principal() -> Principal:
    """FastAPI dependency: the authenticated principal for this request.

    Raises rather than returning None. Reaching this without authentication
    would mean the middleware did not run for a route that is not on the public
    list, which is a wiring bug -- and one that must fail closed rather than
    hand a route an absent identity.
    """

    context = current_authentication()
    if context is None:  # pragma: no cover - unreachable while wiring is correct
        raise authentication_required()
    return context.principal


#: The annotation routes use. Reads as a parameter, enforces at the boundary.
CurrentPrincipal = Annotated[Principal, Depends(current_principal)]
