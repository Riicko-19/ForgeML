"""Minimal synchronous facade over HTTPX's in-process ASGI transport."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence

import httpx
from fastapi import FastAPI

Headers = Mapping[str, str] | Sequence[tuple[str, str]] | None


class ASGITestClient:
    """Issue isolated in-process HTTP requests without Starlette TestClient."""

    def __init__(self, app: FastAPI) -> None:
        self._app = app

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Headers = None,
        content: str | bytes | None = None,
        files: Mapping[str, tuple[str, bytes, str]] | None = None,
    ) -> httpx.Response:
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
