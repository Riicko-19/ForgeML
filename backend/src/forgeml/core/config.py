"""Typed, fail-closed Module 0 configuration."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
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


class PackageLimits(BaseModel):
    """Operator policy bounding work spent on an untrusted .forge archive.

    Every bound is checked before the corresponding bytes are read, so a
    hostile archive cannot make the validator allocate beyond this policy.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_archive_bytes: int = Field(default=268_435_456, ge=1_024, le=17_179_869_184)
    max_uncompressed_bytes: int = Field(
        default=1_073_741_824, ge=1_024, le=68_719_476_736
    )
    max_entries: int = Field(default=10_000, ge=1, le=1_000_000)
    max_compression_ratio: int = Field(default=100, ge=1, le=10_000)
    max_manifest_bytes: int = Field(default=1_048_576, ge=64, le=16_777_216)
    max_schema_nodes: int = Field(default=1_000, ge=1, le=100_000)
    max_schema_depth: int = Field(default=20, ge=1, le=256)

    @model_validator(mode="after")
    def enforce_consistent_bounds(self) -> PackageLimits:
        if self.max_uncompressed_bytes < self.max_archive_bytes:
            raise ValueError(
                "max_uncompressed_bytes must be at least max_archive_bytes"
            )
        if self.max_manifest_bytes > self.max_archive_bytes:
            raise ValueError("max_manifest_bytes must not exceed max_archive_bytes")
        return self


def _require_postgresql(value: SecretStr) -> SecretStr:
    # ADR-009: PostgreSQL is the only supported metadata database. SQLite cannot
    # express the row-locking semantics durable operation claims depend on, so a
    # non-PostgreSQL URL fails closed rather than degrading silently.
    scheme = value.get_secret_value().split("://", 1)[0]
    if scheme not in ("postgresql", "postgresql+psycopg"):
        raise ValueError("database URL must use the postgresql+psycopg driver")
    return value


DatabaseUrl = Annotated[SecretStr, AfterValidator(_require_postgresql)]


class _EnvironmentSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Environment
    log_level: LogLevel = LogLevel.INFO
    bind_host: BindHost = IPv4Address("127.0.0.1")
    bind_port: int = Field(default=8000, ge=1, le=65535)
    graceful_shutdown_seconds: int = Field(default=30, ge=1, le=300)
    artifact_root: Path = Path("storage/artifacts")
    database_url: DatabaseUrl | None = None
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_statement_timeout_ms: int = Field(default=30_000, ge=100, le=600_000)

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
        "artifact_root",
        "database_url",
        "database_pool_size",
        "database_statement_timeout_ms",
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
    artifact_root: Path = Path("storage/artifacts")
    database_url: DatabaseUrl | None = None
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_statement_timeout_ms: int = Field(default=30_000, ge=100, le=600_000)
    package_limits: PackageLimits = PackageLimits()
    service_name: str = Field(default=SERVICE_NAME, frozen=True)
    service_version: str = Field(min_length=1, max_length=64)

    def require_database_url(self) -> str:
        """The metadata database URL, or a fail-closed configuration error.

        Module 0 and Module 1 run without a database, so the setting is optional
        until something actually needs it. Asking for it when it is absent is a
        configuration failure, never a silent fallback.
        """

        if self.database_url is None:
            raise ConfigurationFailure(
                "configuration_invalid",
                (ConfigurationIssue(field="FORGEML_DATABASE_URL", kind="missing"),),
            )
        return self.database_url.get_secret_value()

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
    f"{_PREFIX}ARTIFACT_ROOT": "artifact_root",
    f"{_PREFIX}DATABASE_URL": "database_url",
    f"{_PREFIX}DATABASE_POOL_SIZE": "database_pool_size",
    f"{_PREFIX}DATABASE_STATEMENT_TIMEOUT_MS": "database_statement_timeout_ms",
}

_PACKAGE_LIMIT_FIELDS = {
    f"{_PREFIX}PACKAGE_MAX_ARCHIVE_BYTES": "max_archive_bytes",
    f"{_PREFIX}PACKAGE_MAX_UNCOMPRESSED_BYTES": "max_uncompressed_bytes",
    f"{_PREFIX}PACKAGE_MAX_ENTRIES": "max_entries",
    f"{_PREFIX}PACKAGE_MAX_COMPRESSION_RATIO": "max_compression_ratio",
    f"{_PREFIX}PACKAGE_MAX_MANIFEST_BYTES": "max_manifest_bytes",
    f"{_PREFIX}PACKAGE_MAX_SCHEMA_NODES": "max_schema_nodes",
    f"{_PREFIX}PACKAGE_MAX_SCHEMA_DEPTH": "max_schema_depth",
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


def _safe_issues(
    error: ValidationError, prefix: str = ""
) -> tuple[ConfigurationIssue, ...]:
    issues: list[ConfigurationIssue] = []
    for item in error.errors(
        include_url=False, include_context=False, include_input=False
    ):
        location = ".".join(str(segment) for segment in item["loc"])
        issues.append(
            ConfigurationIssue(
                field=f"{prefix}{location}" if location else "configuration",
                kind=item["type"],
            )
        )
    return tuple(issues)


def load_settings(environment: Mapping[str, str] | None = None) -> AppSettings:
    """Load settings from an explicit mapping or the process environment."""

    source = os.environ if environment is None else environment
    known = _ENVIRONMENT_FIELDS.keys() | _PACKAGE_LIMIT_FIELDS.keys()
    unknown = sorted(
        key for key in source if key.startswith(_PREFIX) and key not in known
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
    limits_raw = {
        field: source[key]
        for key, field in _PACKAGE_LIMIT_FIELDS.items()
        if key in source
    }
    try:
        limits = PackageLimits.model_validate(limits_raw)
    except ValidationError as exc:
        raise ConfigurationFailure(
            "configuration_invalid", _safe_issues(exc, "package_limits.")
        ) from exc

    try:
        env_settings = _EnvironmentSettings.model_validate(raw)
        return AppSettings(
            **env_settings.model_dump(),
            package_limits=limits,
            service_version=resolve_service_version(),
        )
    except ValidationError as exc:
        raise ConfigurationFailure("configuration_invalid", _safe_issues(exc)) from exc
