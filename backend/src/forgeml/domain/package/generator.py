"""Generate a deterministic runtime build context from an inference contract.

Module 4's generator (docs 04 `RuntimeArtifactGenerator`) turns the analyzed
`InferenceContract` into the files needed to build a runtime image: a
Dockerfile, a pinned requirements file, and the runtime adapter that exposes the
package's entrypoint and schemas. Like the analyzer, it is a pure deterministic
function -- no Docker, no filesystem, no network. It generates text; building
and running it belong to Modules 5 and 6.

Determinism is the exit gate: identical `(contract, checksum, runtime,
generator version)` inputs produce byte-identical files and therefore an
identical SHA-256 identity, and any meaningful change to those inputs changes
it. The identity folds in checksum, runtime, and generator version explicitly so
it varies even when they do not appear verbatim in a generated file.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from forgeml.domain.package.models import InferenceContract

GENERATOR_VERSION = "1"

# The runtime base image. A generator input (docs 04 keys identity on "runtime"),
# defaulted so the context is usable; Module 5 supplies the pinned reference.
DEFAULT_RUNTIME_IMAGE = "python:3.11-slim"


@dataclass(frozen=True, slots=True)
class GeneratedBuildContext:
    """A deterministic set of build files plus their content-addressed identity."""

    generator_version: str
    runtime: str
    files: Mapping[str, str]
    identity: str


def _requirements(contract: InferenceContract) -> str:
    # Dependencies are already sorted by the analyzer; one per line, trailing
    # newline, empty when the package declares none.
    return "".join(f"{dependency}\n" for dependency in contract.dependencies)


def _dockerfile(runtime: str) -> str:
    # No CMD: how the adapter is served is the runtime module's concern
    # (Module 6). This context installs dependencies and lays out the source.
    return (
        f"FROM {runtime}\n"
        "WORKDIR /app\n"
        "COPY requirements.txt ./\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n"
        "COPY src/ ./src/\n"
        "COPY forge_adapter.py ./\n"
    )


def _adapter(contract: InferenceContract) -> str:
    # Canonical JSON (sorted keys) keeps the embedded schemas byte-stable across
    # runs. The adapter only wires the entrypoint and schemas; validation and
    # serving are added around it by the runtime module (Module 6).
    input_schema = json.dumps(contract.input_schema, indent=4, sort_keys=True)
    output_schema = json.dumps(contract.output_schema, indent=4, sort_keys=True)
    return (
        '"""Generated ForgeML runtime adapter. Do not edit."""\n\n'
        "import importlib\n\n"
        f"INPUT_SCHEMA = {input_schema}\n\n"
        f"OUTPUT_SCHEMA = {output_schema}\n\n"
        f'_module = importlib.import_module("{contract.entrypoint_module}")\n'
        f'predict = getattr(_module, "{contract.entrypoint_callable}")\n'
    )


def _identity(
    generator_version: str, runtime: str, checksum: str, files: Mapping[str, str]
) -> str:
    payload = json.dumps(
        {
            "generator_version": generator_version,
            "runtime": runtime,
            "checksum": checksum,
            "files": dict(files),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate(
    contract: InferenceContract,
    *,
    checksum: str,
    runtime: str = DEFAULT_RUNTIME_IMAGE,
    generator_version: str = GENERATOR_VERSION,
) -> GeneratedBuildContext:
    """Generate the runtime build context for a contract. Pure and deterministic."""

    files = {
        "Dockerfile": _dockerfile(runtime),
        "requirements.txt": _requirements(contract),
        "forge_adapter.py": _adapter(contract),
    }
    identity = _identity(generator_version, runtime, checksum, files)
    return GeneratedBuildContext(
        generator_version=generator_version,
        runtime=runtime,
        files=files,
        identity=identity,
    )
