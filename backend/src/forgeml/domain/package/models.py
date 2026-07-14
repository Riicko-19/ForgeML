"""Immutable .forge format model for package format version 1.

The manifest models below are the normative shape of forge.yaml. Every level
forbids unknown fields, because docs 04/12 make format version 1 closed: a
package that declares something the platform does not understand is rejected
rather than deployed on a best-effort basis.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)

from forgeml.core.errors import ErrorDetail

FORGE_VERSION = 1
MANIFEST_NAME = "forge.yaml"
SOURCE_ROOT = "src"
VALIDATOR_VERSION = "1"

SUPPORTED_FRAMEWORK = "python-callable"
SUPPORTED_PYTHON = "3.11"

_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"


class Finding(StrEnum):
    """Stable machine codes reported by package validation.

    These codes are part of the external contract (docs 12 error envelope
    details) and may not be renamed without a package major version.
    """

    ARCHIVE_UNREADABLE = "archive_unreadable"
    ARCHIVE_TOO_LARGE = "archive_too_large"
    ARCHIVE_ENTRY_LIMIT_EXCEEDED = "archive_entry_limit_exceeded"
    ARCHIVE_UNCOMPRESSED_LIMIT_EXCEEDED = "archive_uncompressed_limit_exceeded"
    ARCHIVE_COMPRESSION_RATIO_EXCEEDED = "archive_compression_ratio_exceeded"
    ARCHIVE_ENCRYPTED_MEMBER = "archive_encrypted_member"
    ARCHIVE_SYMLINK_MEMBER = "archive_symlink_member"
    ARCHIVE_UNSUPPORTED_MEMBER_TYPE = "archive_unsupported_member_type"
    ARCHIVE_PATH_ABSOLUTE = "archive_path_absolute"
    ARCHIVE_PATH_TRAVERSAL = "archive_path_traversal"
    ARCHIVE_PATH_NOT_UTF8 = "archive_path_not_utf8"
    ARCHIVE_PATH_NOT_NORMALIZED = "archive_path_not_normalized"
    ARCHIVE_DUPLICATE_PATH = "archive_duplicate_path"
    ARCHIVE_SOURCE_ROOT_MISSING = "archive_source_root_missing"

    MANIFEST_MISSING = "manifest_missing"
    MANIFEST_NOT_ROOT_LEVEL = "manifest_not_root_level"
    MANIFEST_TOO_LARGE = "manifest_too_large"
    MANIFEST_MALFORMED = "manifest_malformed"
    MANIFEST_NOT_MAPPING = "manifest_not_mapping"
    MANIFEST_UNKNOWN_FIELD = "manifest_unknown_field"
    MANIFEST_FIELD_MISSING = "manifest_field_missing"
    MANIFEST_FIELD_INVALID = "manifest_field_invalid"

    FORGE_VERSION_UNSUPPORTED = "forge_version_unsupported"
    FRAMEWORK_UNSUPPORTED = "framework_unsupported"
    RUNTIME_PYTHON_UNSUPPORTED = "runtime_python_unsupported"

    ENTRYPOINT_MODULE_MISSING = "entrypoint_module_missing"

    DEPENDENCY_INVALID = "dependency_invalid"
    DEPENDENCY_NOT_PINNED = "dependency_not_pinned"
    DEPENDENCY_DUPLICATE = "dependency_duplicate"

    ASSET_MISSING = "asset_missing"
    ASSET_CHECKSUM_MISMATCH = "asset_checksum_mismatch"

    SCHEMA_INVALID = "schema_invalid"
    SCHEMA_EXTERNAL_REF = "schema_external_ref"
    SCHEMA_UNSUPPORTED_DIALECT = "schema_unsupported_dialect"
    SCHEMA_LIMIT_EXCEEDED = "schema_limit_exceeded"

    FINDINGS_TRUNCATED = "findings_truncated"


class ValidationState(StrEnum):
    """Terminal outcome of validating one archive."""

    VALIDATED = "validated"
    REJECTED = "rejected"


class PackageState(StrEnum):
    """Persisted package lifecycle (docs 04).

    ValidationState is the validator's verdict about one archive; PackageState is
    the durable lifecycle of a stored package. They overlap on the two terminal
    values by design, and `from_validation` is the only sanctioned bridge.
    """

    DRAFT = "draft"
    VALIDATING = "validating"
    VALIDATED = "validated"
    REJECTED = "rejected"

    @classmethod
    def from_validation(cls, state: ValidationState) -> PackageState:
        return cls.VALIDATED if state is ValidationState.VALIDATED else cls.REJECTED


class ArchiveUnreadable(Exception):
    """The bytes are not a readable ZIP container at all."""


def _reject_control_characters(value: str) -> str:
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ValueError("control characters are not allowed")
    return value


Safe = AfterValidator(_reject_control_characters)

DisplayName = Annotated[
    str, StringConstraints(min_length=1, max_length=128, strip_whitespace=True), Safe
]
ShortText = Annotated[
    str, StringConstraints(min_length=1, max_length=64, strip_whitespace=True), Safe
]
DottedModule = Annotated[
    str,
    StringConstraints(
        max_length=200, pattern=r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$"
    ),
]
Identifier = Annotated[
    str, StringConstraints(max_length=128, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
]
RelativePath = Annotated[
    str, StringConstraints(min_length=1, max_length=1024, strip_whitespace=True), Safe
]
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
MetadataKey = Annotated[
    str, StringConstraints(max_length=64, pattern=r"^[a-z][a-z0-9._-]*$")
]
MetadataValue = Annotated[str, StringConstraints(min_length=1, max_length=256), Safe]


class _Section(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())


class ModelSection(_Section):
    """Display identity of the packaged model. Not a deployment key."""

    name: DisplayName
    framework: str
    version: ShortText


class RuntimeSection(_Section):
    """Runtime the package requires; the ADR-008 matrix pins this to 3.11."""

    python: str


class EntrypointSection(_Section):
    """The single executable integration point of a package (ADR-008)."""

    module: DottedModule
    callable: Identifier


class SchemaSection(_Section):
    """A JSON Schema Draft 2020-12 document declared by the package."""

    json_schema: dict[str, Any] = Field(alias="schema")


class AssetSpec(_Section):
    """A model asset carried inside the archive."""

    path: RelativePath
    sha256: Sha256Hex | None = None


class ResourceSpec(_Section):
    """Requested runtime resources, bounded by server policy at deploy time."""

    cpu_millicores: int | None = Field(default=None, ge=1, le=64_000)
    memory_mib: int | None = Field(default=None, ge=1, le=1_048_576)
    pids_limit: int | None = Field(default=None, ge=1, le=32_768)


class ManifestV1(_Section):
    """forge.yaml for format version 1."""

    forge_version: int
    model: ModelSection
    runtime: RuntimeSection
    entrypoint: EntrypointSection
    input: SchemaSection
    output: SchemaSection
    dependencies: tuple[str, ...] = Field(default=(), max_length=500)
    assets: tuple[AssetSpec, ...] = Field(default=(), max_length=500)
    resources: ResourceSpec | None = None
    metadata: dict[MetadataKey, MetadataValue] = Field(
        default_factory=dict, max_length=32
    )


@dataclass(frozen=True, slots=True)
class ArchiveEntry:
    """Header-level facts about one archive member.

    Populated from the ZIP central directory only. No member content has been
    read when these are produced, so the limit rules can run before the
    validator spends bytes on a hostile archive.
    """

    name: str
    is_directory: bool
    is_regular_file: bool
    is_symlink: bool
    is_encrypted: bool
    has_utf8_name: bool
    compressed_size: int
    uncompressed_size: int


@dataclass(frozen=True, slots=True)
class ArchiveInspection:
    """What an archive reader can learn without executing or importing anything."""

    entries: tuple[ArchiveEntry, ...]
    manifest_document: Mapping[str, Any] | None = None
    manifest_fault: Finding | None = None


@dataclass(frozen=True, slots=True)
class PackageValidation:
    """The result of validating one archive. Findings are ordered and stable."""

    state: ValidationState
    validator_version: str
    findings: tuple[ErrorDetail, ...]
    manifest: ManifestV1 | None = None


@dataclass(frozen=True, slots=True)
class Package:
    """A stored package. Checksum and artifact are immutable (ADR-003).

    manifest_version is None until the package has been validated. The bytes are
    stored before anything has parsed them, and recording a format version we
    have not yet read would be a fabricated fact in a durable record.
    """

    id: UUID
    sha256: str
    filename: str
    size_bytes: int
    state: PackageState
    artifact_uri: str
    created_at: datetime
    updated_at: datetime
    manifest_version: int | None = None
    manifest: ManifestV1 | None = None


def is_supported_schema_dialect(value: object) -> bool:
    """Report whether a declared $schema is the one dialect docs 12 allows."""

    return value == _SCHEMA_DIALECT
