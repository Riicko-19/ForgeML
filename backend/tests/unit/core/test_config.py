"""Configuration contract tests."""

from collections.abc import Mapping
from importlib import metadata
from typing import cast

import pytest
from pydantic import ValidationError

from forgeml.core.config import (
    AppSettings,
    ConfigurationFailure,
    Environment,
    LogLevel,
    load_settings,
    resolve_service_version,
)


def test_load_settings_normalizes_and_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")

    settings = load_settings(
        {
            "FORGEML_ENVIRONMENT": " Production ",
            "FORGEML_LOG_LEVEL": " warning ",
        }
    )

    assert settings.environment is Environment.PRODUCTION
    assert settings.log_level is LogLevel.WARNING
    assert str(settings.bind_host) == "127.0.0.1"
    assert settings.bind_port == 8000
    assert settings.graceful_shutdown_seconds == 30
    assert settings.service_name == "forgeml-control-plane"
    assert settings.service_version == "0.1.0"


@pytest.mark.parametrize(
    ("values", "issue_kind"),
    [
        ({}, "missing"),
        ({"FORGEML_ENVIRONMENT": ""}, "enum"),
        ({"FORGEML_ENVIRONMENT": "staging"}, "enum"),
        (
            {"FORGEML_ENVIRONMENT": "test", "FORGEML_BIND_PORT": "0"},
            "greater_than_equal",
        ),
        (
            {"FORGEML_ENVIRONMENT": "test", "FORGEML_BIND_PORT": "65536"},
            "less_than_equal",
        ),
        (
            {"FORGEML_ENVIRONMENT": "test", "FORGEML_BIND_HOST": "localhost"},
            "ip_v4_address",
        ),
        (
            {"FORGEML_ENVIRONMENT": "test", "FORGEML_BIND_HOST": "0.0.0.0"},
            "value_error",
        ),
        (
            {"FORGEML_ENVIRONMENT": "test", "FORGEML_BIND_HOST": "::"},
            "value_error",
        ),
        (
            {
                "FORGEML_ENVIRONMENT": "test",
                "FORGEML_GRACEFUL_SHUTDOWN_SECONDS": " ",
            },
            "value_error",
        ),
    ],
)
def test_load_settings_rejects_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    values: dict[str, str],
    issue_kind: str,
) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")

    with pytest.raises(ConfigurationFailure) as captured:
        load_settings(values)

    assert captured.value.code == "configuration_invalid"
    assert captured.value.issues
    assert captured.value.issues[0].kind == issue_kind


def test_unknown_forgeml_setting_fails_without_value_disclosure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")

    with pytest.raises(ConfigurationFailure) as captured:
        load_settings(
            {
                "FORGEML_ENVIRONMENT": "test",
                "FORGEML_SECRET_TYPO": "do-not-disclose",
            }
        )

    assert captured.value.issues[0].field == "FORGEML_SECRET_TYPO"
    assert "do-not-disclose" not in repr(captured.value.issues)


def test_lowercase_prefix_is_not_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")

    with pytest.raises(ConfigurationFailure) as captured:
        load_settings({"forgeml_environment": "test"})

    assert captured.value.issues[0].kind == "missing"


def test_explicit_mapping_is_not_supplemented_by_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")
    monkeypatch.setenv("FORGEML_LOG_LEVEL", "DEBUG")

    settings = load_settings({"FORGEML_ENVIRONMENT": "test"})

    assert settings.log_level is LogLevel.INFO


def test_non_string_explicit_value_is_validated_without_string_operations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")
    source = cast(
        Mapping[str, str],
        {"FORGEML_ENVIRONMENT": "test", "FORGEML_BIND_PORT": 9000},
    )

    settings = load_settings(source)

    assert settings.bind_port == 9000


def test_settings_are_immutable(settings: AppSettings) -> None:
    with pytest.raises(ValidationError):
        settings.bind_port = 9000


def test_service_identity_is_fixed() -> None:
    with pytest.raises(ValidationError):
        AppSettings(
            environment=Environment.TEST,
            service_name="other",
            service_version="0.1.0",
        )


def test_explicit_valid_service_identity_is_accepted() -> None:
    settings = AppSettings(
        environment=Environment.TEST,
        service_name="forgeml-control-plane",
        service_version="0.1.0",
    )

    assert settings.service_name == "forgeml-control-plane"


@pytest.mark.parametrize("value", ["", "bad version", "x" * 65])
def test_invalid_explicit_service_version_fails(value: str) -> None:
    with pytest.raises(ValidationError):
        AppSettings(environment=Environment.TEST, service_version=value)


def test_resolve_service_version_missing_is_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(_: str) -> str:
        raise metadata.PackageNotFoundError("secret-path")

    monkeypatch.setattr(metadata, "version", missing)

    with pytest.raises(ConfigurationFailure) as captured:
        resolve_service_version()

    assert captured.value.code == "service_metadata_unavailable"
    assert "secret-path" not in str(captured.value)


def test_resolve_service_version_rejects_invalid_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "bad version")

    with pytest.raises(ConfigurationFailure, match="service_metadata_unavailable"):
        resolve_service_version()


def test_resolve_service_version_rejects_non_string_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: None)

    with pytest.raises(ConfigurationFailure, match="service_metadata_unavailable"):
        resolve_service_version()


def test_resolve_service_version_normalizes_unexpected_reader_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failed(_: str) -> str:
        raise RuntimeError("secret /host/path")

    monkeypatch.setattr(metadata, "version", failed)

    with pytest.raises(ConfigurationFailure) as captured:
        resolve_service_version()

    assert captured.value.code == "service_metadata_unavailable"
    assert "secret" not in str(captured.value)
