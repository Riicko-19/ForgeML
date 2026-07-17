"""The analyzer derives a deterministic inference contract from a manifest."""

from __future__ import annotations

from forgeml.domain.package.analyzer import ANALYZER_VERSION, analyze
from forgeml.domain.package.models import InferenceContract, ManifestV1
from tests.packages import SCHEMA_DIALECT, VALID_MANIFEST, manifest


def _analyze(**overrides: object) -> InferenceContract:
    return analyze(ManifestV1.model_validate(manifest(**overrides)))


def test_contract_maps_the_manifest_fields() -> None:
    contract = _analyze()

    assert contract.analyzer_version == ANALYZER_VERSION
    assert contract.framework == "python-callable"
    assert contract.python == "3.11"
    assert contract.entrypoint_module == "model"
    assert contract.entrypoint_callable == "predict"
    assert contract.model_name == "Reference Scorer"
    assert contract.model_version == "1.0.0"


def test_dependencies_are_sorted_for_a_canonical_order() -> None:
    contract = _analyze(dependencies=["numpy==2.1.0", "anyio==4.0.0"])
    assert contract.dependencies == ("anyio==4.0.0", "numpy==2.1.0")


def test_dependency_order_does_not_change_the_contract() -> None:
    forward = _analyze(dependencies=["a==1", "b==2", "c==3"])
    shuffled = _analyze(dependencies=["c==3", "a==1", "b==2"])
    assert forward == shuffled


def test_absent_dependencies_default_to_empty() -> None:
    document = manifest()
    document.pop("dependencies")
    contract = analyze(ManifestV1.model_validate(document))
    assert contract.dependencies == ()


def test_missing_schema_dialect_is_resolved_to_the_supported_one() -> None:
    # VALID_MANIFEST's output schema omits $schema; the contract fills it in.
    assert "$schema" not in VALID_MANIFEST["output"]["schema"]
    contract = _analyze()
    assert contract.output_schema["$schema"] == SCHEMA_DIALECT


def test_declared_schema_dialect_is_preserved() -> None:
    # The input schema already declares the supported dialect; it is untouched.
    assert VALID_MANIFEST["input"]["schema"]["$schema"] == SCHEMA_DIALECT
    contract = _analyze()
    assert contract.input_schema["$schema"] == SCHEMA_DIALECT
    assert contract.input_schema["properties"] == {"value": {"type": "number"}}


def test_normalization_does_not_mutate_the_manifest() -> None:
    parsed = ManifestV1.model_validate(manifest())
    analyze(parsed)
    # The manifest's own output schema still lacks the dialect: the contract
    # deep-copies rather than editing the frozen model's document in place.
    assert "$schema" not in parsed.output.json_schema


def test_analysis_is_deterministic() -> None:
    assert _analyze() == _analyze()
