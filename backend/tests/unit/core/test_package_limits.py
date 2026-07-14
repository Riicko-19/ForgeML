"""Package limits are operator policy loaded through the fail-closed loader."""

from __future__ import annotations

from importlib import metadata

import pytest
from pydantic import ValidationError

from forgeml.core.config import ConfigurationFailure, PackageLimits, load_settings


@pytest.fixture(autouse=True)
def installed_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")


def test_defaults_bound_every_dimension_of_an_untrusted_archive() -> None:
    settings = load_settings({"FORGEML_ENVIRONMENT": "test"})

    limits = settings.package_limits
    assert limits.max_archive_bytes == 268_435_456
    assert limits.max_uncompressed_bytes == 1_073_741_824
    assert limits.max_entries == 10_000
    assert limits.max_compression_ratio == 100
    assert limits.max_schema_depth == 20


def test_limits_are_overridable_from_the_environment() -> None:
    settings = load_settings(
        {
            "FORGEML_ENVIRONMENT": "test",
            "FORGEML_PACKAGE_MAX_ENTRIES": "25",
            "FORGEML_ARTIFACT_ROOT": "/srv/forgeml/artifacts",
        }
    )

    assert settings.package_limits.max_entries == 25
    assert str(settings.artifact_root) == "/srv/forgeml/artifacts"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("FORGEML_PACKAGE_MAX_ENTRIES", "0"),
        ("FORGEML_PACKAGE_MAX_SCHEMA_DEPTH", "-1"),
        ("FORGEML_PACKAGE_MAX_ARCHIVE_BYTES", "not-a-number"),
        ("FORGEML_PACKAGE_MAX_COMPRESSION_RATIO", ""),
    ],
)
def test_an_invalid_limit_fails_closed(key: str, value: str) -> None:
    with pytest.raises(ConfigurationFailure) as captured:
        load_settings({"FORGEML_ENVIRONMENT": "test", key: value})

    assert captured.value.code == "configuration_invalid"
    assert captured.value.issues[0].field.startswith("package_limits.")


def test_limits_that_contradict_each_other_are_rejected() -> None:
    with pytest.raises(ValidationError):
        PackageLimits(max_archive_bytes=2_048, max_uncompressed_bytes=1_024)

    with pytest.raises(ValidationError):
        PackageLimits(max_archive_bytes=2_048, max_manifest_bytes=4_096)


def test_limits_are_immutable() -> None:
    limits = PackageLimits()

    with pytest.raises(ValidationError):
        limits.max_entries = 1
