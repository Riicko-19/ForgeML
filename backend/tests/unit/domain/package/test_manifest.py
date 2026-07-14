"""The manifest model is the closed shape of forge.yaml."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from forgeml.domain.package.models import ManifestV1
from tests.packages import VALID_MANIFEST, manifest


def test_reference_manifest_parses_into_immutable_sections() -> None:
    parsed = ManifestV1.model_validate(VALID_MANIFEST)

    assert parsed.entrypoint.module == "model"
    assert parsed.dependencies == ("numpy==2.1.0",)
    with pytest.raises(ValidationError):
        parsed.forge_version = 2


def test_schema_is_read_from_the_declared_field_name_only() -> None:
    parsed = ManifestV1.model_validate(VALID_MANIFEST)
    assert parsed.input.json_schema["type"] == "object"

    with pytest.raises(ValidationError):
        ManifestV1.model_validate(manifest(input={"json_schema": {"type": "object"}}))


@pytest.mark.parametrize(
    "section",
    [
        {
            "model": {
                "name": "M",
                "framework": "python-callable",
                "version": "1",
                "x": 1,
            }
        },
        {"runtime": {"python": "3.11", "cuda": "12"}},
        {"entrypoint": {"module": "model", "callable": "predict", "args": []}},
    ],
)
def test_unknown_fields_are_rejected_at_every_level(section: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ManifestV1.model_validate(manifest(**section))


def test_control_characters_are_rejected_in_package_authored_text() -> None:
    # A display name is echoed back to operators, so it may not carry an escape
    # sequence or a newline that could forge a log line.
    with pytest.raises(ValidationError):
        ManifestV1.model_validate(
            manifest(
                model={
                    "name": "Model\x1b[31m",
                    "framework": "python-callable",
                    "version": "1.0.0",
                }
            )
        )


def test_metadata_may_not_be_unbounded() -> None:
    with pytest.raises(ValidationError):
        ManifestV1.model_validate(
            manifest(metadata={f"key{index}": "v" for index in range(33)})
        )
