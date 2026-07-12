"""Fail-closed ForgeML process bootstrap."""

from __future__ import annotations

import json
import logging
import signal
import sys
from datetime import UTC, datetime
from types import FrameType

import uvicorn

from forgeml.core.composition import create_application
from forgeml.core.config import ConfigurationFailure, load_settings
from forgeml.core.logging import LoggingConfigurationConflict, configure_logging

_LOGGER = logging.getLogger("forgeml.bootstrap")


class _ShutdownRequested(Exception):
    """Translate Uvicorn's re-raised SIGTERM into a clean process exit."""


def _raise_shutdown_requested(_: int, __: FrameType | None) -> None:
    raise _ShutdownRequested


def _safe_bootstrap_failure(code: str) -> None:
    event = {
        "timestamp": datetime.now(UTC)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z"),
        "severity": "ERROR",
        "service": "forgeml-control-plane",
        "version": "unavailable",
        "environment": "unavailable",
        "component": "forgeml.bootstrap",
        "event": "configuration_invalid",
        "message": "ForgeML startup configuration is invalid.",
        "code": code,
    }
    sys.stderr.write(json.dumps(event, separators=(",", ":")) + "\n")


def main() -> int:
    """Validate configuration and run the single ForgeML ASGI worker."""

    try:
        settings = load_settings()
    except ConfigurationFailure as exc:
        _safe_bootstrap_failure(exc.code)
        return 2

    try:
        configure_logging(settings)
    except LoggingConfigurationConflict:
        _safe_bootstrap_failure("logging_configuration_conflict")
        return 1
    except Exception:
        _safe_bootstrap_failure("logging_configuration_failed")
        return 1

    previous_sigterm = signal.signal(signal.SIGTERM, _raise_shutdown_requested)
    try:
        try:
            app = create_application(settings)
            config = uvicorn.Config(
                app=app,
                host=str(settings.bind_host),
                port=settings.bind_port,
                workers=1,
                reload=False,
                proxy_headers=False,
                access_log=False,
                log_config=None,
                timeout_graceful_shutdown=settings.graceful_shutdown_seconds,
            )
            server = uvicorn.Server(config)
            server.run()
        except (KeyboardInterrupt, _ShutdownRequested):
            _LOGGER.info(
                "Server shutdown requested.",
                extra={"event": "server_shutdown_requested"},
            )
            return 0
        except (Exception, SystemExit) as exc:
            _LOGGER.error(
                "Server startup failed.",
                extra={
                    "event": "server_startup_failed",
                    "exception_type": type(exc).__name__,
                },
            )
            return 1
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
    if not server.started:
        _LOGGER.error(
            "Server startup failed.",
            extra={"event": "server_startup_failed"},
        )
        return 1
    return 0
