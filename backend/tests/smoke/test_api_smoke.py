"""The ForgeML golden path, end to end, against a real server.

Every other HTTP test in this suite drives the application in-process over
ASGI, which is fast and proves the contract but never binds a socket. This one
starts the shipped entry point as its own process, talks to it over the
network, and walks the single path a user actually takes: upload a package,
poll the operation, read the result back. It is the automated form of the
manual Postman run that used to gate every module.

It is deliberately the thinnest tier in the suite. It answers one question --
"is the real thing alive and does the main path work?" -- and nothing else.
Findings, error envelopes, idempotency conflicts, and pagination are all
proven far more cheaply in tests/integration/api/test_packages_api.py, and
belong there. Resist adding to this file: everything here costs ~10 seconds of
every checkpoint, forever.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import httpx
import pytest

from forgeml.application.identity.services import ApiKeyAdministration
from forgeml.core.config import load_settings
from forgeml.infrastructure.database.provider import DatabaseProvider
from tests.integration.api.conftest import database_url

EXAMPLE = Path(__file__).parents[3] / "examples" / "hello-model.forge"

BOOT_TIMEOUT = 20.0
OPERATION_TIMEOUT = 20.0
TERMINAL = frozenset({"succeeded", "failed"})


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@contextmanager
def _serve(artifact_root: Path) -> Iterator[str]:
    """Run `python -m forgeml` on a free port and yield its base URL.

    This repeats the process handling in tests/integration/api/test_process_signals.py
    rather than sharing it. That test asserts on signal delivery and exit codes
    and owns its own output capture; the overlap is a dozen lines of Popen and
    a poll loop. Extract a common helper when a second smoke test needs one --
    a shared fixture with a single caller is just a longer way to write this.

    Output is inherited rather than piped: nothing here asserts on logs, pytest
    captures the file descriptors anyway and prints them when a test fails, and
    a pipe nobody drains is a deadlock waiting for a chatty server.
    """

    port = _free_port()
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("FORGEML_")
    }
    environment.update(
        {
            "FORGEML_ENVIRONMENT": "test",
            "FORGEML_BIND_PORT": str(port),
            "FORGEML_DATABASE_URL": database_url(),
            # Keep the uploaded artifact in the test's own temporary tree
            # instead of the developer's working copy under backend/storage.
            "FORGEML_ARTIFACT_ROOT": str(artifact_root),
        }
    )

    process = subprocess.Popen([sys.executable, "-m", "forgeml"], env=environment)
    base_url = f"http://127.0.0.1:{port}"
    try:
        _await_boot(process, base_url)
        yield base_url
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _await_boot(process: subprocess.Popen[bytes], base_url: str) -> None:
    """Block until the process serves liveness, or explain why it never did."""

    deadline = time.monotonic() + BOOT_TIMEOUT
    with httpx.Client(trust_env=False) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(
                    f"the control plane exited with {process.returncode} during "
                    f"startup; its output is captured above"
                )
            try:
                if client.get(f"{base_url}/healthz", timeout=0.5).status_code == 200:
                    return
            except httpx.TransportError:
                time.sleep(0.05)
    pytest.fail(f"the control plane did not serve /healthz within {BOOT_TIMEOUT:.0f}s")


def _await_operation(client: httpx.Client, operation_id: str) -> dict[str, Any]:
    """Poll one operation until it reaches a terminal state (ADR-006)."""

    deadline = time.monotonic() + OPERATION_TIMEOUT
    while time.monotonic() < deadline:
        response = client.get(f"/v1/operations/{operation_id}")
        assert response.status_code == 200, response.text
        operation: dict[str, Any] = response.json()
        if operation["state"] in TERMINAL:
            return operation
        time.sleep(0.05)
    pytest.fail(
        f"operation {operation_id} never settled within {OPERATION_TIMEOUT:.0f}s"
    )


def _smoke_credential() -> str:
    """Mint a key in the same database the server under test will read.

    The smoke test drives a real process over real HTTP, so it authenticates
    the way an operator does: `python -m forgeml.identity create`, then a bearer
    header. ADR-025 left no bypass, and this test is the proof that the
    documented first-run path actually works end to end.
    """

    settings = load_settings(
        {"FORGEML_ENVIRONMENT": "test", "FORGEML_DATABASE_URL": database_url()}
    )
    provider = DatabaseProvider(settings)
    try:
        return ApiKeyAdministration(provider.unit_of_work).create(name="smoke")
    finally:
        provider.dispose()


def test_the_golden_path_works_against_a_running_server(
    migrated: None, tmp_path: Path
) -> None:
    if not EXAMPLE.is_file():
        pytest.fail(f"{EXAMPLE} is missing. Run `make example` (or `make verify`).")
    archive = EXAMPLE.read_bytes()

    with (
        _serve(tmp_path / "artifacts") as base_url,
        httpx.Client(
            base_url=base_url,
            trust_env=False,
            timeout=10.0,
            headers={"Authorization": f"Bearer {_smoke_credential()}"},
        ) as client,
    ):
        assert client.get("/healthz").status_code == 200

        ready = client.get("/readyz")
        assert ready.status_code == 200, ready.text

        accepted = client.post(
            "/v1/packages",
            headers={"Idempotency-Key": "smoke-1"},
            files={"file": (EXAMPLE.name, archive, "application/octet-stream")},
        )
        assert accepted.status_code == 202, accepted.text

        operation = _await_operation(client, accepted.json()["id"])
        assert operation["state"] == "succeeded", operation
        assert operation["result"]["validation_state"] == "validated", operation
        package_id = operation["result"]["package_id"]

        read = client.get(f"/v1/packages/{package_id}")
        assert read.status_code == 200, read.text
        package = read.json()
        assert package["validation_state"] == "validated", package
        # The manifest the platform parsed is the one we packed, not a default.
        assert package["manifest"]["model"]["name"] == "Hello Model", package
