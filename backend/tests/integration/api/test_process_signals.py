"""Real-process signal and graceful-shutdown integration."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time

import httpx

from tests.integration.api.conftest import database_url


def _available_loopback_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def test_sigterm_stops_installed_process_without_traceback() -> None:
    port = _available_loopback_port()
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("FORGEML_")
    }
    environment.update(
        {
            "FORGEML_ENVIRONMENT": "test",
            "FORGEML_BIND_PORT": str(port),
            # Since Module 3 the control plane recovers abandoned operations at
            # startup (ADR-016) and fails closed without its database (docs 11),
            # so a real process needs a real one.
            "FORGEML_DATABASE_URL": database_url(),
        }
    )
    process = subprocess.Popen(
        [sys.executable, "-m", "forgeml"],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout = ""
    stderr = ""
    try:
        deadline = time.monotonic() + 10
        response: httpx.Response | None = None
        with httpx.Client(trust_env=False) as client:
            while time.monotonic() < deadline and process.poll() is None:
                try:
                    response = client.get(
                        f"http://127.0.0.1:{port}/healthz",
                        timeout=0.5,
                    )
                    if response.status_code == 200:
                        break
                except httpx.TransportError:
                    time.sleep(0.05)

        assert response is not None and response.status_code == 200
        process.send_signal(signal.SIGTERM)
        return_code = process.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        stdout, stderr = process.communicate(timeout=5)

    assert return_code == 0
    combined = stdout + stderr
    assert "Traceback" not in combined
    assert "KeyboardInterrupt" not in combined
