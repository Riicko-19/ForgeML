"""Server-owned request correlation and bounded request logging."""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from forgeml.api.error_handlers import internal_error_response
from forgeml.core.correlation import (
    new_request_id,
    reset_request_id,
    set_request_id,
)

_LOGGER = logging.getLogger("forgeml.request")


class RequestContextMiddleware:
    """Own the canonical request ID for one HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        scope["headers"] = [
            (name, value)
            for name, value in scope.get("headers", [])
            if name.lower() != b"x-request-id"
        ]
        request_id = new_request_id()
        token = set_request_id(request_id)
        started_at = perf_counter()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = int(message["status"])
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self._app(scope, receive, send_with_request_id)
        except asyncio.CancelledError:
            status_code = 499
            raise
        except Exception as exc:
            _LOGGER.error(
                "Unexpected request failure.",
                extra={
                    "event": "request_failed",
                    "exception_type": type(exc).__name__,
                },
            )
            if response_started:
                raise
            await internal_error_response()(scope, receive, send_with_request_id)
        finally:
            route = scope.get("route")
            route_template = getattr(route, "path", "unmatched")
            _LOGGER.info(
                "Request completed.",
                extra={
                    "event": "request_completed",
                    "method": str(scope.get("method", "")),
                    "route": route_template,
                    "status_code": status_code,
                    "duration_ms": (perf_counter() - started_at) * 1000,
                },
            )
            reset_request_id(token)
