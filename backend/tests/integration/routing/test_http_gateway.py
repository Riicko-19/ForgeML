"""The real HTTP prediction gateway, against a local server.

Proves the adapter's HTTP mechanics -- request shape, response decoding, and
failure classification -- without Docker, by pointing it at a standard-library
server bound on localhost. Runtime reachability in production is a Docker-network
topology concern (ADR-010), not the adapter's logic.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any, ClassVar

import pytest

from forgeml.domain.routing.ports import (
    PredictionUnavailable,
    PredictionUpstreamError,
)
from forgeml.infrastructure.runtime.http_gateway import HttpPredictionGateway


class _Handler(BaseHTTPRequestHandler):
    status: ClassVar[int] = 200
    body: ClassVar[bytes] = b'{"result": {"score": 1.0}}'
    seen: ClassVar[dict[str, Any]] = {}

    def log_message(self, *_args: object) -> None:
        pass

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        _Handler.seen = {
            "path": self.path,
            "body": json.loads(self.rfile.read(length) or b"{}"),
        }
        self.send_response(_Handler.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(_Handler.body)))
        self.end_headers()
        self.wfile.write(_Handler.body)


@pytest.fixture
def server() -> Iterator[str]:
    _Handler.status = 200
    _Handler.body = b'{"result": {"score": 1.0}}'
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = str(httpd.server_address[0]), httpd.server_address[1]
        yield f"http://{host}:{port}"
    finally:
        httpd.shutdown()
        thread.join()
        httpd.server_close()


def test_forwards_and_decodes_the_response(server: str) -> None:
    result = HttpPredictionGateway().predict(server, {"value": 3})

    assert result == {"result": {"score": 1.0}}
    assert _Handler.seen["path"] == "/predict"  # the gateway appends /predict
    assert _Handler.seen["body"] == {"value": 3}


def test_a_non_2xx_response_is_an_upstream_error(server: str) -> None:
    _Handler.status = 500
    with pytest.raises(PredictionUpstreamError):
        HttpPredictionGateway().predict(server, {"value": 3})


def test_an_unreadable_body_is_an_upstream_error(server: str) -> None:
    _Handler.body = b"not json"
    with pytest.raises(PredictionUpstreamError):
        HttpPredictionGateway().predict(server, {"value": 3})


def test_an_unreachable_endpoint_is_unavailable() -> None:
    # Nothing is listening on this port.
    with pytest.raises(PredictionUnavailable):
        HttpPredictionGateway().predict("http://127.0.0.1:1", {"value": 3})
