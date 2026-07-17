"""Derive the normalized inference contract from a validated manifest.

Module 4's analyzer (docs 04 `PackageAnalyzer`) is a pure function of a manifest
that has already passed validation: it reads no archive, opens no database, and
touches no Docker or network. It follows the same shape as `validate_package`
in rules.py -- deterministic logic is a function here, not a Protocol, because
there is no I/O boundary to abstract.

Its job is narrow: take a `ManifestV1` and produce the `InferenceContract` the
runtime generator (and, later, the deployment module) needs to serve the model.
Everything it returns is derivable from the manifest, so the same manifest
always yields the same contract -- the property the generator's artifact
identity depends on.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from forgeml.domain.package.models import (
    InferenceContract,
    ManifestV1,
    is_supported_schema_dialect,
)

ANALYZER_VERSION = "1"

_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"


def _normalized_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Return the schema with the supported dialect made explicit.

    Validation accepts a schema that omits `$schema` (rules.py only rejects a
    *wrong* dialect); the runtime needs it unambiguous, so the contract fills in
    the one dialect docs 12 allows when the package left it out.
    """

    normalized = copy.deepcopy(dict(schema))
    declared = normalized.get("$schema")
    if declared is None or not is_supported_schema_dialect(declared):
        normalized["$schema"] = _SCHEMA_DIALECT
    return normalized


def analyze(manifest: ManifestV1) -> InferenceContract:
    """Derive the inference contract from a validated manifest. Pure."""

    return InferenceContract(
        analyzer_version=ANALYZER_VERSION,
        framework=manifest.model.framework,
        python=manifest.runtime.python,
        entrypoint_module=manifest.entrypoint.module,
        entrypoint_callable=manifest.entrypoint.callable,
        dependencies=tuple(sorted(manifest.dependencies)),
        input_schema=_normalized_schema(manifest.input.json_schema),
        output_schema=_normalized_schema(manifest.output.json_schema),
        model_name=manifest.model.name,
        model_version=manifest.model.version,
    )
