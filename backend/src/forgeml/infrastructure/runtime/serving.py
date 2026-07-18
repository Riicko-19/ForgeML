"""The in-container serving harness Module 6 adds around Module 4's adapter.

Module 4's generator deliberately emits no server and no CMD -- its docstring
says "how the adapter is served is the runtime module's concern (Module 6)".
This module supplies that concern: a dependency-free HTTP harness that imports
the generated `forge_adapter` (its `predict` callable and its schemas) and
serves two endpoints on the container-internal port:

    GET  /health   readiness for the Docker HEALTHCHECK and `inspect`
    POST /predict  the model's own prediction endpoint

The harness is standard-library only (`http.server`), so it adds nothing to the
runtime image beyond the package's own pinned dependencies, and it runs happily
as a non-root user on an unprivileged port. Routing *to* this endpoint across
versions is Module 7's concern; a single runtime serving its own endpoint is
this module's.

`FORGE_SERVER_SOURCE` is written verbatim into the build context as
`forge_server.py`; `augment_dockerfile` appends the copy, environment,
health check, and command that the frozen generated Dockerfile leaves to us.
"""

from __future__ import annotations

RUNTIME_PORT = 8000

# Written into the image as /app/forge_server.py. Kept as a string (not an
# imported module) because it executes inside the runtime container, never in
# the control plane. Standard library only.
FORGE_SERVER_SOURCE = '''\
"""ForgeML runtime serving harness (Module 6). Standard library only."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Importing the generated adapter binds `predict` and the schemas. If the
# package cannot import, this raises at startup and the container exits
# non-zero -- which the control plane observes as a failed start, never a
# runtime that reports healthy while broken.
import forge_adapter

_MAX_BODY_BYTES = 10 * 1024 * 1024


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        # Access logging is Module 8's concern; stay silent here.
        pass

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {"status": "ok"})
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/predict":
            self._send(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length < 0 or length > _MAX_BODY_BYTES:
            self._send(413, {"error": "payload_too_large"})
            return
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"error": "invalid_json"})
            return
        try:
            result = forge_adapter.predict(payload)
        except Exception as error:  # noqa: BLE001 - the model owns its errors
            self._send(500, {"error": "prediction_failed", "detail": str(error)[:200]})
            return
        self._send(200, {"result": result})


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8000), _Handler)  # noqa: S104
    server.serve_forever()


if __name__ == "__main__":
    main()
'''


def augment_dockerfile(generated_dockerfile: str) -> str:
    """Append the serving layer the frozen generated Dockerfile leaves to us.

    The generated Dockerfile installs dependencies and lays out `src/` and
    `forge_adapter.py` but sets no CMD (Module 4, by design). We copy the
    harness in, put `src/` on the path, declare a health check the runtime
    manager can observe, and start the server. `PYTHONDONTWRITEBYTECODE` keeps
    the read-only root filesystem happy.
    """

    healthcheck = (
        "HEALTHCHECK --interval=2s --timeout=3s --start-period=2s --retries=30 "
        'CMD ["python", "-c", "import urllib.request, sys; '
        "sys.exit(0 if urllib.request.urlopen("
        f"'http://127.0.0.1:{RUNTIME_PORT}/health').status == 200 else 1)\"]"
    )
    layer = (
        "COPY forge_server.py ./\n"
        "ENV PYTHONPATH=/app/src PYTHONDONTWRITEBYTECODE=1\n"
        f"EXPOSE {RUNTIME_PORT}\n"
        f"{healthcheck}\n"
        'CMD ["python", "forge_server.py"]\n'
    )
    if not generated_dockerfile.endswith("\n"):
        generated_dockerfile += "\n"
    return generated_dockerfile + layer
