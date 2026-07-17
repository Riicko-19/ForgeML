"""The generator produces a deterministic build context and a stable identity."""

from __future__ import annotations

import hashlib

from forgeml.domain.package.analyzer import analyze
from forgeml.domain.package.generator import (
    DEFAULT_RUNTIME_IMAGE,
    GENERATOR_VERSION,
    generate,
)
from forgeml.domain.package.models import InferenceContract, ManifestV1
from tests.packages import manifest

CHECKSUM = "a" * 64


def _contract(**overrides: object) -> InferenceContract:
    return analyze(ManifestV1.model_validate(manifest(**overrides)))


def test_generation_produces_the_three_build_files() -> None:
    context = generate(_contract(), checksum=CHECKSUM)
    assert set(context.files) == {"Dockerfile", "requirements.txt", "forge_adapter.py"}


def test_dockerfile_pins_the_runtime_and_lays_out_the_source() -> None:
    context = generate(_contract(), checksum=CHECKSUM)
    dockerfile = context.files["Dockerfile"]
    assert dockerfile.startswith(f"FROM {DEFAULT_RUNTIME_IMAGE}\n")
    assert "COPY forge_adapter.py ./" in dockerfile


def test_requirements_lists_the_sorted_dependencies() -> None:
    context = generate(
        _contract(dependencies=["numpy==2.1.0", "anyio==4.0.0"]), checksum=CHECKSUM
    )
    assert context.files["requirements.txt"] == "anyio==4.0.0\nnumpy==2.1.0\n"


def test_adapter_wires_the_entrypoint_and_embeds_the_schemas() -> None:
    context = generate(_contract(), checksum=CHECKSUM)
    adapter = context.files["forge_adapter.py"]
    assert 'importlib.import_module("model")' in adapter
    assert 'getattr(_module, "predict")' in adapter
    assert "INPUT_SCHEMA = {" in adapter
    assert "OUTPUT_SCHEMA = {" in adapter


def test_identity_is_a_sha256_of_the_canonical_payload() -> None:
    context = generate(_contract(), checksum=CHECKSUM)
    assert len(context.identity) == 64
    assert int(context.identity, 16) >= 0  # valid hex


def test_generation_is_deterministic() -> None:
    first = generate(_contract(), checksum=CHECKSUM)
    second = generate(_contract(), checksum=CHECKSUM)
    assert first == second
    assert first.identity == second.identity


def test_cosmetic_manifest_changes_keep_the_same_identity() -> None:
    # Dependency order is normalized by the analyzer, so it must not move identity.
    forward = generate(_contract(dependencies=["a==1", "b==2"]), checksum=CHECKSUM)
    shuffled = generate(_contract(dependencies=["b==2", "a==1"]), checksum=CHECKSUM)
    assert forward.identity == shuffled.identity


def test_a_different_checksum_changes_identity() -> None:
    base = generate(_contract(), checksum=CHECKSUM)
    other = generate(_contract(), checksum="b" * 64)
    assert base.identity != other.identity


def test_a_different_runtime_changes_identity() -> None:
    base = generate(_contract(), checksum=CHECKSUM)
    other = generate(_contract(), checksum=CHECKSUM, runtime="python:3.11-alpine")
    assert base.identity != other.identity


def test_a_different_generator_version_changes_identity() -> None:
    base = generate(_contract(), checksum=CHECKSUM)
    other = generate(_contract(), checksum=CHECKSUM, generator_version="2")
    assert base.identity != other.identity


def test_a_different_contract_changes_identity() -> None:
    base = generate(_contract(), checksum=CHECKSUM)
    other = generate(_contract(dependencies=["numpy==2.2.0"]), checksum=CHECKSUM)
    assert base.identity != other.identity


def test_identity_matches_an_independent_recomputation() -> None:
    context = generate(_contract(), checksum=CHECKSUM)
    import json

    payload = json.dumps(
        {
            "generator_version": GENERATOR_VERSION,
            "runtime": DEFAULT_RUNTIME_IMAGE,
            "checksum": CHECKSUM,
            "files": dict(context.files),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    assert context.identity == hashlib.sha256(payload.encode("utf-8")).hexdigest()
