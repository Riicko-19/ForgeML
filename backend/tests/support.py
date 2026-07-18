"""Minimal synchronous facade over HTTPX's in-process ASGI transport."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from uuid import UUID

import httpx
from fastapi import FastAPI

from forgeml.api.authentication import AuthenticationMiddleware
from forgeml.application.identity.services import ApiKeyAdministration, ApiKeyVerifier
from forgeml.application.unit_of_work import UnitOfWork
from forgeml.core.config import AppSettings
from forgeml.domain.identity.models import (
    ActorType,
    AuthenticationContext,
    AuthenticationMethod,
    Principal,
)

Headers = Mapping[str, str] | Sequence[tuple[str, str]] | None

#: The principal service-level tests act as. A value, not a mock: these tests
#: assert on what lands in the audit trail, so the identity has to be real.
TEST_PRINCIPAL = Principal(actor_type=ActorType.OPERATOR, actor_id="test-operator")


#: Accepted by StubVerifier and by nothing else. Shaped like a real token so
#: that parsing is still exercised.
STUB_TOKEN = f"forge_{'0' * 16}_stub-credential-for-tests"


class StubVerifier:
    """A CredentialVerifier for tests that run without a database.

    Module 0's tests compose the application with no metadata database, so no
    key can be minted for them -- but their routes still authenticate, because
    ADR-025 left no bypass to switch off. This is a fake implementation of a
    port, exactly like FakeRuntimeManager, and it exists only inside the test
    suite. It is not a second code path in the application: production composes
    ApiKeyVerifier and has no way to reach this.
    """

    def verify(self, presented: str) -> AuthenticationContext | None:
        if presented != STUB_TOKEN:
            return None
        return AuthenticationContext(
            principal=TEST_PRINCIPAL,
            credential_id=UUID(int=0),
            method=AuthenticationMethod.API_KEY,
        )


def stub_application(settings: AppSettings) -> tuple[FastAPI, str]:
    """A fully composed app whose verifier needs no database, and its token."""

    from forgeml.core.composition import create_application

    return create_application(settings, verifier=StubVerifier()), STUB_TOKEN


def credential_for(app: FastAPI) -> str:
    """Mint a key against a fully composed app's own database.

    For tests that build the real application through `create_application`,
    where authentication is already wired and only a usable credential is
    missing.
    """

    container = app.state.container
    return ApiKeyAdministration(container.database.unit_of_work).create(
        name="test-suite"
    )


def authenticate(app: FastAPI, unit_of_work: UnitOfWork) -> str:
    """Wire real authentication onto a test app and return a working token.

    Deliberately the production verifier over the in-memory store rather than a
    stub. ADR-025 removed the bypass so that the authenticated path is the only
    path, and a test double here would quietly reintroduce the second path that
    decision exists to prevent.

    Call before adding RequestContextMiddleware: add_middleware prepends, so
    request context must be added last to end up outermost.
    """

    token = ApiKeyAdministration(lambda: unit_of_work).create(name="test-suite")
    app.add_middleware(
        AuthenticationMiddleware, verifier=ApiKeyVerifier(lambda: unit_of_work)
    )
    return token


class ASGITestClient:
    """Issue isolated in-process HTTP requests without Starlette TestClient."""

    def __init__(self, app: FastAPI, credential: str | None = None) -> None:
        self._app = app
        self._credential = credential

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Headers = None,
        content: str | bytes | None = None,
        files: Mapping[str, tuple[str, bytes, str]] | None = None,
    ) -> httpx.Response:
        if self._credential is not None:
            merged = dict(headers or {})
            # An explicit Authorization in a test wins, so a test can still
            # present a bad credential on purpose.
            merged.setdefault("Authorization", f"Bearer {self._credential}")
            headers = merged

        async def send() -> httpx.Response:
            transport = httpx.ASGITransport(
                app=self._app,
                raise_app_exceptions=False,
            )
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://forgeml.test",
            ) as client:
                return await client.request(
                    method,
                    path,
                    headers=headers,
                    content=content,
                    files=files,
                )

        return asyncio.run(send())

    def get(self, path: str, *, headers: Headers = None) -> httpx.Response:
        return self.request("GET", path, headers=headers)

    def post(
        self,
        path: str,
        *,
        headers: Headers = None,
        content: str | bytes | None = None,
    ) -> httpx.Response:
        return self.request("POST", path, headers=headers, content=content)
