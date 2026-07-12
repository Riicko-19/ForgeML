"""Structured logging policy tests."""

import json
import logging
from types import TracebackType

import pytest

from forgeml.core import logging as forge_logging
from forgeml.core.config import AppSettings, Environment, LogLevel
from forgeml.core.correlation import reset_request_id, set_request_id
from forgeml.core.logging import (
    JsonEventFormatter,
    LoggingConfigurationConflict,
    configure_logging,
)


def _record(
    name: str,
    message: str,
    *,
    event: object = "test_event",
    exc_info: (
        tuple[type[BaseException], BaseException, TracebackType | None] | None
    ) = None,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name=name,
        level=logging.ERROR,
        pathname="/secret/path.py",
        lineno=12,
        msg=message,
        args=(),
        exc_info=exc_info,
    )
    record.event = event
    return record


def test_internal_event_has_exact_safe_base_fields(settings: AppSettings) -> None:
    formatter = JsonEventFormatter(settings)
    token = set_request_id("00000000-0000-4000-8000-000000000001")

    payload = json.loads(formatter.format(_record("forgeml.test", "Safe message.")))
    reset_request_id(token)

    assert set(payload) == {
        "timestamp",
        "severity",
        "service",
        "version",
        "environment",
        "component",
        "event",
        "message",
        "request_id",
    }
    assert payload["message"] == "Safe message."
    assert payload["timestamp"].endswith("Z")
    assert "/secret/path.py" not in json.dumps(payload)


def test_third_party_message_and_arguments_are_suppressed(
    settings: AppSettings,
) -> None:
    formatter = JsonEventFormatter(settings)
    record = _record("uvicorn.error", "secret=/host/path")

    payload = json.loads(formatter.format(record))

    assert payload["event"] == "third_party_event"
    assert payload["message"] == "Third-party log event suppressed."
    assert "secret" not in json.dumps(payload)
    assert "path" not in json.dumps(payload)


@pytest.mark.parametrize("name", ["forgemleak", "forgeml_vendor"])
def test_near_prefix_logger_is_not_trusted(
    settings: AppSettings,
    name: str,
) -> None:
    payload = json.loads(
        JsonEventFormatter(settings).format(_record(name, "secret=/host/path"))
    )

    assert payload["event"] == "third_party_event"
    assert payload["message"] == "Third-party log event suppressed."
    assert "secret" not in json.dumps(payload)


@pytest.mark.parametrize(
    ("level", "severity"),
    [
        (0, "DEBUG"),
        (logging.DEBUG, "DEBUG"),
        (logging.INFO, "INFO"),
        (35, "WARNING"),
        (logging.ERROR, "ERROR"),
        (60, "CRITICAL"),
    ],
)
def test_severity_is_normalized(
    settings: AppSettings,
    level: int,
    severity: str,
) -> None:
    record = _record("forgeml.test", "Safe.")
    record.levelno = level
    record.levelname = "CUSTOM"

    payload = json.loads(JsonEventFormatter(settings).format(record))

    assert payload["severity"] == severity


def test_exception_text_and_traceback_are_not_serialized(
    settings: AppSettings,
) -> None:
    formatter = JsonEventFormatter(settings)
    error = RuntimeError("secret /host/path")
    record = _record(
        "forgeml.test",
        "Unexpected request failure.",
        exc_info=(RuntimeError, error, None),
    )

    payload = json.loads(formatter.format(record))

    assert payload["exception_type"] == "RuntimeError"
    assert "secret" not in json.dumps(payload)
    assert "/host/path" not in json.dumps(payload)


def test_event_and_fields_are_bounded(settings: AppSettings) -> None:
    formatter = JsonEventFormatter(settings)
    record = _record("forgeml." + "x" * 200, "x" * 600, event="BAD EVENT")
    record.method = "M" * 30
    record.route = "/" + "x" * 300
    record.status_code = "200"
    record.duration_ms = -1

    payload = json.loads(formatter.format(record))

    assert payload["event"] == "invalid_log_event"
    assert len(payload["component"]) == 128
    assert payload["component"].endswith("...")
    assert len(payload["message"]) == 512
    assert payload["method"].endswith("...")
    assert len(payload["route"]) == 256
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 0.0


def test_explicit_exception_type_is_bounded(settings: AppSettings) -> None:
    record = _record("forgeml.test", "Safe.")
    record.exception_type = "X" * 200

    payload = json.loads(JsonEventFormatter(settings).format(record))

    assert len(payload["exception_type"]) == 128
    assert payload["exception_type"].endswith("...")


def test_configure_logging_is_idempotent_and_rejects_conflict(
    monkeypatch: pytest.MonkeyPatch,
    settings: AppSettings,
) -> None:
    root = logging.getLogger()
    prior_handlers = list(root.handlers)
    prior_level = root.level
    monkeypatch.setattr(forge_logging, "_configured_fingerprint", None)

    try:
        configure_logging(settings)
        first_handlers = list(root.handlers)
        configure_logging(settings)
        assert root.handlers == first_handlers

        conflicting = settings.model_copy(update={"log_level": LogLevel.DEBUG})
        with pytest.raises(LoggingConfigurationConflict):
            configure_logging(conflicting)
    finally:
        root.handlers[:] = prior_handlers
        root.setLevel(prior_level)


def test_formatter_rejects_unreachable_extra_field(settings: AppSettings) -> None:
    formatter = JsonEventFormatter(settings)

    with pytest.raises(AssertionError):
        formatter._normalize_extra("unknown", "value")


def test_log_level_settings_are_rendered() -> None:
    settings = AppSettings(
        environment=Environment.DEVELOPMENT,
        log_level=LogLevel.DEBUG,
        service_version="0.1.0",
    )
    payload = json.loads(
        JsonEventFormatter(settings).format(_record("forgeml.test", "Safe."))
    )

    assert payload["environment"] == "development"
