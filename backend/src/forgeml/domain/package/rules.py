"""Package validation policy.

Every rule here is a pure function over header-level facts and the parsed
manifest document. Nothing in this module imports, executes, or deserializes
package content, which is the acceptance gate for the package owner.

Findings are emitted in a fixed stage order (archive, manifest, compatibility
matrix, entrypoint, dependencies, schemas, assets) and within a stage in
archive or declaration order, so the same archive always produces the same
ordered findings.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Mapping
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from pydantic import ValidationError

from forgeml.core.config import PackageLimits
from forgeml.core.errors import ErrorDetail
from forgeml.domain.package.models import (
    SOURCE_ROOT,
    SUPPORTED_FRAMEWORK,
    SUPPORTED_PYTHON,
    VALIDATOR_VERSION,
    ArchiveEntry,
    ArchiveInspection,
    Finding,
    ManifestV1,
    PackageValidation,
    SchemaSection,
    ValidationState,
    is_supported_schema_dialect,
)

MAX_FINDINGS = 50
_MAX_SEGMENT = 128

# A small file of repeated bytes compresses far past any sane ratio, so the
# ratio rule only applies once a member is large enough for the expansion to
# matter. ponytail: fixed 1 MiB floor; make it policy if a real package trips it.
_RATIO_FLOOR_BYTES = 1_048_576

_PYDANTIC_FINDINGS = {
    "extra_forbidden": Finding.MANIFEST_UNKNOWN_FIELD,
    "missing": Finding.MANIFEST_FIELD_MISSING,
}


def _safe_segment(value: str) -> str:
    """Make an archive-supplied name safe to place in an error path."""

    cleaned = "".join(
        character
        for character in unicodedata.normalize("NFC", value)
        if not unicodedata.category(character).startswith("C")
    )
    return cleaned[:_MAX_SEGMENT] or "?"


def _detail(
    code: Finding, message: str, path: tuple[str | int, ...] | None = None
) -> ErrorDetail:
    return ErrorDetail(code=code.value, message=message, path=path)


def _normalize(name: str) -> str:
    return unicodedata.normalize("NFC", name).rstrip("/")


def _path_findings(entry: ArchiveEntry) -> list[ErrorDetail]:
    name = entry.name
    where = (_safe_segment(name),)
    findings: list[ErrorDetail] = []

    if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        findings.append(
            _detail(
                Finding.ARCHIVE_PATH_ABSOLUTE,
                "archive member path must be relative",
                where,
            )
        )
    segments = _normalize(name).split("/")
    if any(segment == ".." for segment in segments):
        findings.append(
            _detail(
                Finding.ARCHIVE_PATH_TRAVERSAL,
                "archive member path must not traverse outside the archive",
                where,
            )
        )
    if "\\" in name or any(segment in ("", ".") for segment in segments):
        findings.append(
            _detail(
                Finding.ARCHIVE_PATH_NOT_NORMALIZED,
                "archive member path must be normalized with forward slashes",
                where,
            )
        )
    return findings


def _entry_findings(
    entries: tuple[ArchiveEntry, ...], limits: PackageLimits
) -> list[ErrorDetail]:
    if len(entries) > limits.max_entries:
        return [
            _detail(
                Finding.ARCHIVE_ENTRY_LIMIT_EXCEEDED,
                "archive declares more members than policy allows",
            )
        ]

    findings: list[ErrorDetail] = []
    seen: set[str] = set()
    total_uncompressed = 0

    for entry in entries:
        where = (_safe_segment(entry.name),)
        total_uncompressed += entry.uncompressed_size

        if not entry.has_utf8_name:
            findings.append(
                _detail(
                    Finding.ARCHIVE_PATH_NOT_UTF8,
                    "archive member path must be UTF-8 encoded",
                    where,
                )
            )
        if entry.is_encrypted:
            findings.append(
                _detail(
                    Finding.ARCHIVE_ENCRYPTED_MEMBER,
                    "archive must not contain encrypted members",
                    where,
                )
            )
        if entry.is_symlink:
            findings.append(
                _detail(
                    Finding.ARCHIVE_SYMLINK_MEMBER,
                    "archive must not contain symbolic links",
                    where,
                )
            )
        elif not (entry.is_directory or entry.is_regular_file):
            findings.append(
                _detail(
                    Finding.ARCHIVE_UNSUPPORTED_MEMBER_TYPE,
                    "archive may contain only regular files and directories",
                    where,
                )
            )
        findings.extend(_path_findings(entry))

        key = _normalize(entry.name)
        if key in seen:
            findings.append(
                _detail(
                    Finding.ARCHIVE_DUPLICATE_PATH,
                    "archive must not contain duplicate member paths",
                    where,
                )
            )
        seen.add(key)

        if (
            entry.compressed_size > 0
            and entry.uncompressed_size > _RATIO_FLOOR_BYTES
            and entry.uncompressed_size / entry.compressed_size
            > limits.max_compression_ratio
        ):
            findings.append(
                _detail(
                    Finding.ARCHIVE_COMPRESSION_RATIO_EXCEEDED,
                    "archive member expands beyond the allowed compression ratio",
                    where,
                )
            )

    if total_uncompressed > limits.max_uncompressed_bytes:
        findings.append(
            _detail(
                Finding.ARCHIVE_UNCOMPRESSED_LIMIT_EXCEEDED,
                "archive expands beyond the allowed uncompressed size",
            )
        )
    if not any(
        _normalize(entry.name).startswith(f"{SOURCE_ROOT}/") for entry in entries
    ):
        findings.append(
            _detail(
                Finding.ARCHIVE_SOURCE_ROOT_MISSING,
                f"archive must contain a {SOURCE_ROOT}/ tree",
            )
        )
    return findings


def _manifest_findings(error: ValidationError) -> list[ErrorDetail]:
    findings: list[ErrorDetail] = []
    for item in error.errors(
        include_url=False, include_context=False, include_input=False
    ):
        code = _PYDANTIC_FINDINGS.get(item["type"], Finding.MANIFEST_FIELD_INVALID)
        path = tuple(
            _safe_segment(segment) if isinstance(segment, str) else segment
            for segment in item["loc"]
        )
        findings.append(_detail(code, _safe_segment(item["msg"]), path or None))
    return findings


def _matrix_findings(manifest: ManifestV1) -> list[ErrorDetail]:
    findings: list[ErrorDetail] = []
    if manifest.forge_version != 1:
        findings.append(
            _detail(
                Finding.FORGE_VERSION_UNSUPPORTED,
                "only forge_version 1 is supported",
                ("forge_version",),
            )
        )
    if manifest.model.framework != SUPPORTED_FRAMEWORK:
        findings.append(
            _detail(
                Finding.FRAMEWORK_UNSUPPORTED,
                f"only the {SUPPORTED_FRAMEWORK} framework is supported",
                ("model", "framework"),
            )
        )
    if manifest.runtime.python != SUPPORTED_PYTHON:
        findings.append(
            _detail(
                Finding.RUNTIME_PYTHON_UNSUPPORTED,
                f"only Python {SUPPORTED_PYTHON} is supported",
                ("runtime", "python"),
            )
        )
    return findings


def _entrypoint_findings(
    manifest: ManifestV1, files: frozenset[str]
) -> list[ErrorDetail]:
    relative = manifest.entrypoint.module.replace(".", "/")
    candidates = (
        f"{SOURCE_ROOT}/{relative}.py",
        f"{SOURCE_ROOT}/{relative}/__init__.py",
    )
    if any(candidate in files for candidate in candidates):
        return []
    return [
        _detail(
            Finding.ENTRYPOINT_MODULE_MISSING,
            f"entrypoint module is not present under {SOURCE_ROOT}/",
            ("entrypoint", "module"),
        )
    ]


def _dependency_findings(dependencies: Iterable[str]) -> list[ErrorDetail]:
    findings: list[ErrorDetail] = []
    seen: set[str] = set()

    for index, raw in enumerate(dependencies):
        path: tuple[str | int, ...] = ("dependencies", index)
        try:
            requirement = Requirement(raw)
        except InvalidRequirement:
            findings.append(
                _detail(
                    Finding.DEPENDENCY_INVALID,
                    "dependency is not a valid PEP 508 requirement",
                    path,
                )
            )
            continue

        specifiers = list(requirement.specifier)
        if (
            requirement.url
            or requirement.marker
            or requirement.extras
            or len(specifiers) != 1
            or specifiers[0].operator != "=="
            or specifiers[0].version.endswith(".*")
        ):
            findings.append(
                _detail(
                    Finding.DEPENDENCY_NOT_PINNED,
                    "dependency must be an exact name==version pin",
                    path,
                )
            )
            continue

        name = canonicalize_name(requirement.name)
        if name in seen:
            findings.append(
                _detail(
                    Finding.DEPENDENCY_DUPLICATE,
                    "dependency is declared more than once",
                    path,
                )
            )
        seen.add(name)
    return findings


def _schema_findings(
    section: SchemaSection, field: str, limits: PackageLimits
) -> list[ErrorDetail]:
    document = section.json_schema
    path: tuple[str | int, ...] = (field, "schema")
    findings: list[ErrorDetail] = []

    declared = document.get("$schema")
    if declared is not None and not is_supported_schema_dialect(declared):
        findings.append(
            _detail(
                Finding.SCHEMA_UNSUPPORTED_DIALECT,
                "schema must declare the JSON Schema Draft 2020-12 dialect",
                path,
            )
        )

    # The walk runs before the validator: a schema deeper than policy would
    # otherwise recurse inside jsonschema before any limit could reject it.
    nodes = 0
    external_ref = False
    stack: list[tuple[Any, int]] = [(document, 1)]
    while stack:
        node, depth = stack.pop()
        nodes += 1
        if nodes > limits.max_schema_nodes or depth > limits.max_schema_depth:
            findings.append(
                _detail(
                    Finding.SCHEMA_LIMIT_EXCEEDED,
                    "schema exceeds the allowed node or depth limit",
                    path,
                )
            )
            return findings
        if isinstance(node, Mapping):
            reference = node.get("$ref")
            if isinstance(reference, str) and not reference.startswith("#"):
                external_ref = True
            stack.extend((value, depth + 1) for value in node.values())
        elif isinstance(node, list):
            stack.extend((value, depth + 1) for value in node)

    if external_ref:
        findings.append(
            _detail(
                Finding.SCHEMA_EXTERNAL_REF,
                "schema may reference only local JSON Pointer targets",
                path,
            )
        )

    try:
        Draft202012Validator.check_schema(document)
    except SchemaError:
        findings.append(
            _detail(
                Finding.SCHEMA_INVALID,
                "schema is not a valid JSON Schema Draft 2020-12 document",
                path,
            )
        )
    return findings


def _asset_findings(manifest: ManifestV1, files: frozenset[str]) -> list[ErrorDetail]:
    return [
        _detail(
            Finding.ASSET_MISSING,
            "declared asset is not present in the archive",
            ("assets", index),
        )
        for index, asset in enumerate(manifest.assets)
        if _normalize(asset.path) not in files
    ]


def asset_checksum_findings(
    expected: Mapping[str, str], actual: Mapping[str, str]
) -> tuple[ErrorDetail, ...]:
    """Compare declared asset checksums against the archive's actual bytes."""

    findings = [
        _detail(
            Finding.ASSET_CHECKSUM_MISMATCH,
            "declared asset checksum does not match the archive content",
            ("assets", _safe_segment(path)),
        )
        for path, digest in sorted(expected.items())
        if actual.get(path) != digest
    ]
    return tuple(findings)


def _reject(findings: list[ErrorDetail]) -> PackageValidation:
    if len(findings) > MAX_FINDINGS:
        findings = [
            *findings[:MAX_FINDINGS],
            _detail(
                Finding.FINDINGS_TRUNCATED,
                "further findings were omitted; fix the reported ones first",
            ),
        ]
    return PackageValidation(
        state=ValidationState.REJECTED,
        validator_version=VALIDATOR_VERSION,
        findings=tuple(findings),
    )


def unreadable_archive() -> PackageValidation:
    """Reject bytes that are not a readable archive container at all."""

    return _reject(
        [
            _detail(
                Finding.ARCHIVE_UNREADABLE,
                "archive is not a readable ZIP container",
            )
        ]
    )


def rejected_with(
    validation: PackageValidation, extra: tuple[ErrorDetail, ...]
) -> PackageValidation:
    """Reject an otherwise valid package because a content check failed."""

    return _reject([*validation.findings, *extra])


def validate_package(
    inspection: ArchiveInspection, limits: PackageLimits
) -> PackageValidation:
    """Validate one inspected archive against the format version 1 contract.

    Stages stop at the first failing one: a manifest cannot be trusted from an
    archive whose structure is unsafe, and cross-checks cannot run against a
    manifest that did not parse.
    """

    archive = _entry_findings(inspection.entries, limits)
    if archive:
        return _reject(archive)

    if inspection.manifest_document is None:
        fault = inspection.manifest_fault or Finding.MANIFEST_MISSING
        return _reject(
            [_detail(fault, "archive does not contain a usable root forge.yaml")]
        )

    try:
        manifest = ManifestV1.model_validate(inspection.manifest_document)
    except ValidationError as error:
        return _reject(_manifest_findings(error))

    matrix = _matrix_findings(manifest)
    if matrix:
        return _reject(matrix)

    files = frozenset(
        _normalize(entry.name) for entry in inspection.entries if entry.is_regular_file
    )
    findings = [
        *_entrypoint_findings(manifest, files),
        *_dependency_findings(manifest.dependencies),
        *_schema_findings(manifest.input, "input", limits),
        *_schema_findings(manifest.output, "output", limits),
        *_asset_findings(manifest, files),
    ]
    if findings:
        return _reject(findings)

    return PackageValidation(
        state=ValidationState.VALIDATED,
        validator_version=VALIDATOR_VERSION,
        findings=(),
        manifest=manifest,
    )
