"""Findings and manifests must survive a round trip through the database.

A finding whose path is dropped on the way out is a contract break that no
schema constraint would catch (docs 12 renders findings as error-envelope
details).
"""

from __future__ import annotations

import pytest

from forgeml.core.config import AppSettings, ConfigurationFailure, Environment
from forgeml.core.errors import ErrorDetail
from forgeml.domain.package.models import ManifestV1
from forgeml.infrastructure.database.engine import create_database_engine
from forgeml.infrastructure.database.mappers import (
    finding_from_json,
    finding_to_json,
    manifest_to_json,
)
from tests.packages import VALID_MANIFEST


@pytest.mark.parametrize(
    "detail",
    [
        ErrorDetail(code="dependency_not_pinned", message="not pinned", path=None),
        ErrorDetail(code="asset_missing", message="absent", path=("assets", 0)),
        ErrorDetail(code="schema_invalid", message="bad", path=("output", "schema")),
    ],
)
def test_a_finding_survives_a_round_trip(detail: ErrorDetail) -> None:
    assert finding_from_json(finding_to_json(detail)) == detail


def test_a_manifest_round_trips_under_its_wire_names() -> None:
    manifest = ManifestV1.model_validate(VALID_MANIFEST)

    document = manifest_to_json(manifest)

    assert document is not None
    # `schema`, not `json_schema`: dumping by field name would produce a
    # document the frozen manifest model refuses to read back.
    assert "schema" in document["input"]
    assert ManifestV1.model_validate(document) == manifest


def test_an_absent_manifest_maps_to_null() -> None:
    assert manifest_to_json(None) is None


def test_an_engine_cannot_be_built_without_a_database_url() -> None:
    settings = AppSettings(environment=Environment.TEST, service_version="0.1.0")

    with pytest.raises(ConfigurationFailure, match="configuration_invalid"):
        create_database_engine(settings)
