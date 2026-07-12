"""Bounded structured process logging."""

from __future__ import annotations

import json
import logging
import re
import threading
import unicodedata
from datetime import UTC, datetime
from typing import Final

from forgeml.core.config import AppSettings
from forgeml.core.correlation import current_request_id

_MAX_COMPONENT: Final = 128
_MAX_EVENT: Final = 64
_MAX_MESSAGE: Final = 512
_MAX_EXCEPTION_TYPE: Final = 128
_EVENT_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_INTERNAL_LOGGER_PREFIX = "forgeml"
_SEVERITIES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_ALLOWED_EXTRA_FIELDS = (
    "exception_type",
    "method",
    "route",
    "status_code",
    "duration_ms",
)

_configuration_lock = threading.Lock()
_configured_fingerprint: tuple[str, str, str, str] | None = None


class LoggingConfigurationConflict(RuntimeError):
    """Raised when process logging is reconfigured incompatibly."""


def _strip_controls(value: str) -> str:
    return "".join(
        " " if unicodedata.category(character).startswith("C") else character
        for character in value
    )


def _bounded(value: str, maximum: int) -> str:
    clean = _strip_controls(value)
    if len(clean) <= maximum:
        return clean
    return f"{clean[: maximum - 3]}..."


class JsonEventFormatter(logging.Formatter):
    """Render a strict allowlisted JSON event."""

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings

    def format(self, record: logging.LogRecord) -> str:
        internal = record.name == _INTERNAL_LOGGER_PREFIX or record.name.startswith(
            f"{_INTERNAL_LOGGER_PREFIX}."
        )
        message = (
            record.getMessage() if internal else "Third-party log event suppressed."
        )
        raw_event = (
            getattr(record, "event", "log_event") if internal else "third_party_event"
        )
        event = raw_event if isinstance(raw_event, str) else "invalid_log_event"
        if not _EVENT_PATTERN.fullmatch(event):
            event = "invalid_log_event"

        payload: dict[str, object] = {
            "timestamp": (
                datetime.fromtimestamp(record.created, UTC)
                .isoformat(timespec="microseconds")
                .replace("+00:00", "Z")
            ),
            "severity": self._severity(record.levelno),
            "service": self._settings.service_name,
            "version": self._settings.service_version,
            "environment": self._settings.environment.value,
            "component": _bounded(record.name or "root", _MAX_COMPONENT),
            "event": event[:_MAX_EVENT],
            "message": _bounded(message, _MAX_MESSAGE),
        }
        request_id = current_request_id()
        if request_id is not None:
            payload["request_id"] = request_id

        if internal:
            for field in _ALLOWED_EXTRA_FIELDS:
                value = getattr(record, field, None)
                if value is not None:
                    payload[field] = self._normalize_extra(field, value)
            if (
                record.exc_info is not None
                and record.exc_info[0] is not None
                and "exception_type" not in payload
            ):
                payload["exception_type"] = _bounded(
                    record.exc_info[0].__name__,
                    _MAX_EXCEPTION_TYPE,
                )

        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _severity(level: int) -> str:
        if level >= logging.CRITICAL:
            return _SEVERITIES[4]
        if level >= logging.ERROR:
            return _SEVERITIES[3]
        if level >= logging.WARNING:
            return _SEVERITIES[2]
        if level >= logging.INFO:
            return _SEVERITIES[1]
        return _SEVERITIES[0]

    @staticmethod
    def _normalize_extra(field: str, value: object) -> object:
        if field == "method":
            return _bounded(str(value), 16)
        if field == "route":
            return _bounded(str(value), 256)
        if field == "exception_type":
            return _bounded(str(value), _MAX_EXCEPTION_TYPE)
        if field == "status_code":
            return int(str(value))
        if field == "duration_ms":
            return round(max(0.0, float(str(value))), 3)
        raise AssertionError("unreachable allowlisted logging field")


def configure_logging(settings: AppSettings) -> None:
    """Configure process logging once for an immutable settings fingerprint."""

    global _configured_fingerprint
    fingerprint = (
        settings.service_name,
        settings.service_version,
        settings.environment.value,
        settings.log_level.value,
    )
    with _configuration_lock:
        if _configured_fingerprint == fingerprint:
            return
        if _configured_fingerprint is not None:
            raise LoggingConfigurationConflict(
                "process logging is already configured differently"
            )

        handler = logging.StreamHandler()
        handler.setFormatter(JsonEventFormatter(settings))
        root = logging.getLogger()
        root.handlers[:] = [handler]
        root.setLevel(settings.log_level.value)
        logging.getLogger("uvicorn.access").disabled = True
        _configured_fingerprint = fingerprint
