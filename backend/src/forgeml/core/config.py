"""Typed, fail-closed Module 0 configuration."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata
from ipaddress import IPv4Address, IPv6Address
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

SERVICE_NAME = "forgeml-control-plane"
_DISTRIBUTION_NAME = "forgeml"
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9.+!-]{1,64}$")
_PREFIX = "FORGEML_"


class Environment(StrEnum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Supported process log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class ConfigurationIssue:
    """A safe configuration finding without an input value."""

    field: str
    kind: str


class ConfigurationFailure(Exception):
    """Fail-closed configuration error safe to classify at bootstrap."""

    def __init__(
        self,
        code: str,
        issues: tuple[ConfigurationIssue, ...] = (),
    ) -> None:
        super().__init__(code)
        self.code = code
        self.issues = issues


def _reject_wildcard_host(
    value: IPv4Address | IPv6Address,
) -> IPv4Address | IPv6Address:
    if value.is_unspecified:
        raise ValueError("wildcard bind addresses are not allowed")
    return value


BindHost = Annotated[IPv4Address | IPv6Address, AfterValidator(_reject_wildcard_host)]


class _EnvironmentSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Environment
    log_level: LogLevel = LogLevel.INFO
    bind_host: BindHost = IPv4Address("127.0.0.1")
    bind_port: int = Field(default=8000, ge=1, le=65535)
    graceful_shutdown_seconds: int = Field(default=30, ge=1, le=300)

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator(
        "bind_host",
        "bind_port",
        "graceful_shutdown_seconds",
        mode="before",
    )
    @classmethod
    def reject_empty_values(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("empty values are not allowed")
        return value


class AppSettings(BaseModel):
    """Immutable settings consumed by composition and bootstrap."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    environment: Environment
    log_level: LogLevel = LogLevel.INFO
    bind_host: BindHost = IPv4Address("127.0.0.1")
    bind_port: int = Field(default=8000, ge=1, le=65535)
    graceful_shutdown_seconds: int = Field(default=30, ge=1, le=300)
    service_name: str = Field(default=SERVICE_NAME, frozen=True)
    service_version: str = Field(min_length=1, max_length=64)

    @field_validator("service_name")
    @classmethod
    def enforce_service_name(cls, value: str) -> str:
        if value != SERVICE_NAME:
            raise ValueError("service_name is fixed")
        return value

    @field_validator("service_version")
    @classmethod
    def validate_service_version(cls, value: str) -> str:
        if not _VERSION_PATTERN.fullmatch(value):
            raise ValueError("invalid service version")
        return value


_ENVIRONMENT_FIELDS = {
    f"{_PREFIX}ENVIRONMENT": "environment",
    f"{_PREFIX}LOG_LEVEL": "log_level",
    f"{_PREFIX}BIND_HOST": "bind_host",
    f"{_PREFIX}BIND_PORT": "bind_port",
    f"{_PREFIX}GRACEFUL_SHUTDOWN_SECONDS": "graceful_shutdown_seconds",
}


def resolve_service_version() -> str:
    """Resolve and validate the installed ForgeML distribution version."""

    try:
        value = metadata.version(_DISTRIBUTION_NAME)
    except Exception as exc:
        raise ConfigurationFailure("service_metadata_unavailable") from exc
    if not isinstance(value, str) or not _VERSION_PATTERN.fullmatch(value):
        raise ConfigurationFailure("service_metadata_unavailable")
    return value


def _safe_issues(error: ValidationError) -> tuple[ConfigurationIssue, ...]:
    issues: list[ConfigurationIssue] = []
    for item in error.errors(
        include_url=False, include_context=False, include_input=False
    ):
        location = ".".join(str(segment) for segment in item["loc"])
        issues.append(
            ConfigurationIssue(field=location or "configuration", kind=item["type"])
        )
    return tuple(issues)


def load_settings(environment: Mapping[str, str] | None = None) -> AppSettings:
    """Load Module 0 settings from an explicit mapping or process environment."""

    source = os.environ if environment is None else environment
    unknown = sorted(
        key
        for key in source
        if key.startswith(_PREFIX) and key not in _ENVIRONMENT_FIELDS
    )
    if unknown:
        issues = tuple(
            ConfigurationIssue(field=key, kind="unknown_setting") for key in unknown
        )
        raise ConfigurationFailure("configuration_invalid", issues)

    raw = {
        field: source[key]
        for key, field in _ENVIRONMENT_FIELDS.items()
        if key in source
    }
    try:
        env_settings = _EnvironmentSettings.model_validate(raw)
        return AppSettings(
            **env_settings.model_dump(),
            service_version=resolve_service_version(),
        )
    except ValidationError as exc:
        raise ConfigurationFailure("configuration_invalid", _safe_issues(exc)) from exc
