"""Request middleware lifecycle tests."""

import asyncio
import io
import json
import logging
from contextlib import suppress

import pytest
from starlette.types import Message, Receive, Scope, Send

from forgeml.api.middleware import RequestContextMiddleware
from forgeml.core.config import AppSettings
from forgeml.core.correlation import current_request_id
from forgeml.core.logging import JsonEventFormatter
from tests.support import ASGITestClient, stub_application


def test_request_completion_record_is_safe(
    settings: AppSettings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app, token = stub_application(settings)
    client = ASGITestClient(app, credential=token)

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonEventFormatter(settings))
    logger = logging.getLogger("forgeml.request")
    logger.addHandler(handler)
    try:
        with caplog.at_level(logging.INFO, logger="forgeml.request"):
            response = client.get("/healthz?secret=value")
    finally:
        logger.removeHandler(handler)

    payload = json.loads(stream.getvalue())
    assert payload["route"] == "/healthz"
    assert payload["method"] == "GET"
    assert payload["status_code"] == 200
    assert payload["request_id"] == response.headers["x-request-id"]
    assert "secret" not in str(payload)
    assert current_request_id() is None


def test_cancelled_request_cleans_context() -> None:
    async def cancelled(_: Scope, __: Receive, ___: Send) -> None:
        raise asyncio.CancelledError

    middleware = RequestContextMiddleware(cancelled)

    async def invoke() -> None:
        scope = {"type": "http", "method": "GET", "path": "/"}
        with suppress(asyncio.CancelledError):
            await middleware(scope, _receive, _send)

    asyncio.run(invoke())
    assert current_request_id() is None


def test_concurrent_requests_receive_distinct_context() -> None:
    observed: list[str | None] = []

    async def inner(_: Scope, __: Receive, send: Send) -> None:
        observed.append(current_request_id())
        await asyncio.sleep(0)
        observed.append(current_request_id())
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = RequestContextMiddleware(inner)
    scope = {"type": "http", "method": "GET", "path": "/"}

    async def run() -> None:
        await asyncio.gather(
            middleware(scope.copy(), _receive, _send),
            middleware(scope.copy(), _receive, _send),
        )

    asyncio.run(run())

    assert observed[0] != observed[1]
    assert observed[0] == observed[2]
    assert observed[1] == observed[3]
    assert current_request_id() is None


def test_non_http_scope_passes_through_without_context() -> None:
    called = False

    async def inner(_: Scope, __: Receive, ___: Send) -> None:
        nonlocal called
        called = True
        assert current_request_id() is None

    middleware = RequestContextMiddleware(inner)
    asyncio.run(middleware({"type": "lifespan"}, _receive, _send))

    assert called is True


def test_failure_after_response_start_is_reraised_and_cleans_context() -> None:
    async def broken(_: Scope, __: Receive, send: Send) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        raise RuntimeError("secret")

    middleware = RequestContextMiddleware(broken)

    async def invoke() -> None:
        with pytest.raises(RuntimeError, match="secret"):
            await middleware(
                {"type": "http", "method": "GET", "path": "/"},
                _receive,
                _send,
            )

    asyncio.run(invoke())
    assert current_request_id() is None


@pytest.mark.parametrize("value", [b"", b"\xff", b"x" * 129])
def test_untrusted_request_id_variants_are_removed(value: bytes) -> None:
    observed: list[tuple[bytes, bytes]] = []

    async def inner(scope: Scope, _: Receive, send: Send) -> None:
        observed.extend(scope.get("headers", []))
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = RequestContextMiddleware(inner)
    scope: Scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"x-request-id", value)],
    }
    asyncio.run(middleware(scope, _receive, _send))

    assert observed == []


async def _receive() -> dict[str, object]:
    return {"type": "http.request", "body": b"", "more_body": False}


async def _send(_: Message) -> None:
    return None
