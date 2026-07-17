"""The .forge reference fixture matrix.

Each case drives a real archive through the real artifact store, the real ZIP
reader, and the real validator, and asserts the stable finding code a client
would receive. These codes are the package contract; changing one is a package
major version, not a refactor.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from forgeml.application.package.validate_package import PackageValidationService
from forgeml.core.config import PackageLimits
from forgeml.domain.package.models import Finding, PackageValidation, ValidationState
from forgeml.infrastructure.package.zip_archive import ZipArchiveReader
from forgeml.infrastructure.storage.artifact_store import FilesystemArtifactStore
from tests.packages import (
    DEFAULT_FILES,
    ENTRYPOINT_SOURCE,
    build_forge,
    manifest,
    patch_general_purpose_flags,
    symlink_member,
)

Validate = Callable[[bytes], PackageValidation]

WEIGHTS = b"reference weights"
WEIGHTS_SHA256 = hashlib.sha256(WEIGHTS).hexdigest()


@pytest.fixture
def validate(tmp_path: Path) -> Validate:
    limits = PackageLimits()
    store = FilesystemArtifactStore(tmp_path)
    service = PackageValidationService(store, ZipArchiveReader(), limits)

    def run(archive: bytes) -> PackageValidation:
        stored = store.put(io.BytesIO(archive), limits)
        return service.validate(stored.sha256)

    return run


def _deep_schema(depth: int) -> dict[str, Any]:
    root: dict[str, Any] = {"type": "object"}
    node = root
    for _ in range(depth):
        child: dict[str, Any] = {"type": "object"}
        node["properties"] = {"child": child}
        node = child
    return root


def _with_assets(*assets: dict[str, Any]) -> bytes:
    return build_forge(
        manifest(assets=list(assets)),
        files={**DEFAULT_FILES, "assets/weights.bin": WEIGHTS},
    )


def _zip_bomb() -> bytes:
    return build_forge(files={**DEFAULT_FILES, "src/filler.bin": b"\x00" * 8_388_608})


def _non_utf8_name() -> bytes:
    archive = build_forge(
        files={"src/model.py": ENTRYPOINT_SOURCE, "src/café.py": b"x"},
        compression=zipfile.ZIP_STORED,
    )
    return patch_general_purpose_flags(archive, set_bits=0, clear_bits=0x800)


def _encrypted_member() -> bytes:
    archive = build_forge(compression=zipfile.ZIP_STORED)
    return patch_general_purpose_flags(archive, set_bits=0x1, clear_bits=0)


REFERENCE_MATRIX: list[tuple[str, bytes, Finding]] = [
    (
        "not an archive",
        b"this is not a zip container",
        Finding.ARCHIVE_UNREADABLE,
    ),
    (
        "manifest absent",
        build_forge(include_manifest=False),
        Finding.MANIFEST_MISSING,
    ),
    (
        "manifest is not parsable yaml",
        build_forge(raw_manifest=b"forge_version: [1\n"),
        Finding.MANIFEST_MALFORMED,
    ),
    (
        "manifest expands yaml aliases",
        build_forge(raw_manifest=b"anchor: &a [1, 2]\nalias: *a\n"),
        Finding.MANIFEST_MALFORMED,
    ),
    (
        "manifest is not a mapping",
        build_forge(raw_manifest=b"- forge_version\n- 1\n"),
        Finding.MANIFEST_NOT_MAPPING,
    ),
    (
        "manifest declares an unknown field",
        build_forge(manifest(gpu={"count": 1})),
        Finding.MANIFEST_UNKNOWN_FIELD,
    ),
    (
        "manifest omits a required section",
        build_forge(
            {key: value for key, value in manifest().items() if key != "runtime"}
        ),
        Finding.MANIFEST_FIELD_MISSING,
    ),
    (
        "manifest field has the wrong shape",
        build_forge(manifest(entrypoint={"module": "model", "callable": "9invalid"})),
        Finding.MANIFEST_FIELD_INVALID,
    ),
    (
        "unsupported forge version",
        build_forge(manifest(forge_version=2)),
        Finding.FORGE_VERSION_UNSUPPORTED,
    ),
    (
        "unsupported framework",
        build_forge(
            manifest(
                model={"name": "M", "framework": "onnx", "version": "1.0.0"},
            )
        ),
        Finding.FRAMEWORK_UNSUPPORTED,
    ),
    (
        "unsupported python runtime",
        build_forge(manifest(runtime={"python": "3.12"})),
        Finding.RUNTIME_PYTHON_UNSUPPORTED,
    ),
    (
        "path traversal member",
        build_forge(hostile=[(zipfile.ZipInfo("../escape.py"), b"x")]),
        Finding.ARCHIVE_PATH_TRAVERSAL,
    ),
    (
        "absolute path member",
        build_forge(hostile=[(zipfile.ZipInfo("/etc/passwd"), b"x")]),
        Finding.ARCHIVE_PATH_ABSOLUTE,
    ),
    (
        "symlink member",
        build_forge(hostile=[symlink_member("src/link.py", "/etc/passwd")]),
        Finding.ARCHIVE_SYMLINK_MEMBER,
    ),
    (
        "duplicate member",
        build_forge(
            files={"src/model.py": ENTRYPOINT_SOURCE},
            hostile=[(zipfile.ZipInfo("src/model.py"), b"shadow")],
        ),
        Finding.ARCHIVE_DUPLICATE_PATH,
    ),
    (
        "encrypted member",
        _encrypted_member(),
        Finding.ARCHIVE_ENCRYPTED_MEMBER,
    ),
    (
        "non utf-8 member name",
        _non_utf8_name(),
        Finding.ARCHIVE_PATH_NOT_UTF8,
    ),
    (
        "zip bomb expansion ratio",
        _zip_bomb(),
        Finding.ARCHIVE_COMPRESSION_RATIO_EXCEEDED,
    ),
    (
        "no source tree",
        build_forge(files={"lib/model.py": ENTRYPOINT_SOURCE}),
        Finding.ARCHIVE_SOURCE_ROOT_MISSING,
    ),
    (
        "entrypoint module absent",
        build_forge(files={"src/other.py": ENTRYPOINT_SOURCE}),
        Finding.ENTRYPOINT_MODULE_MISSING,
    ),
    (
        "dependency is not a requirement",
        build_forge(manifest(dependencies=["-e ."])),
        Finding.DEPENDENCY_INVALID,
    ),
    (
        "dependency is a range",
        build_forge(manifest(dependencies=["numpy>=2.1.0"])),
        Finding.DEPENDENCY_NOT_PINNED,
    ),
    (
        "dependency is a direct url",
        build_forge(
            manifest(dependencies=["numpy @ https://example.invalid/numpy.whl"])
        ),
        Finding.DEPENDENCY_NOT_PINNED,
    ),
    (
        "dependency is declared twice",
        build_forge(manifest(dependencies=["numpy==2.1.0", "NumPy==2.2.0"])),
        Finding.DEPENDENCY_DUPLICATE,
    ),
    (
        "schema is not a valid document",
        build_forge(manifest(output={"schema": {"type": 5}})),
        Finding.SCHEMA_INVALID,
    ),
    (
        "schema references an external document",
        build_forge(
            manifest(output={"schema": {"$ref": "https://example.invalid/s.json"}})
        ),
        Finding.SCHEMA_EXTERNAL_REF,
    ),
    (
        "schema declares an unsupported dialect",
        build_forge(
            manifest(
                output={
                    "schema": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                    }
                }
            )
        ),
        Finding.SCHEMA_UNSUPPORTED_DIALECT,
    ),
    (
        "schema exceeds the depth limit",
        build_forge(manifest(output={"schema": _deep_schema(40)})),
        Finding.SCHEMA_LIMIT_EXCEEDED,
    ),
    (
        "declared asset is absent",
        _with_assets({"path": "assets/absent.bin"}),
        Finding.ASSET_MISSING,
    ),
    (
        "declared asset checksum does not match",
        _with_assets({"path": "assets/weights.bin", "sha256": "0" * 64}),
        Finding.ASSET_CHECKSUM_MISMATCH,
    ),
]


@pytest.mark.parametrize(
    ("archive", "expected"),
    [
        pytest.param(archive, expected, id=name)
        for name, archive, expected in REFERENCE_MATRIX
    ],
)
def test_reference_matrix_rejects_with_stable_code(
    validate: Validate, archive: bytes, expected: Finding
) -> None:
    result = validate(archive)

    assert result.state is ValidationState.REJECTED
    assert result.manifest is None
    # A rejected package is never analyzed, so it carries no inference contract.
    assert result.contract is None
    assert expected.value in {finding.code for finding in result.findings}


def test_minimal_valid_package_is_accepted(validate: Validate) -> None:
    result = validate(build_forge())

    assert result.state is ValidationState.VALIDATED
    assert result.findings == ()
    assert result.manifest is not None
    assert result.manifest.entrypoint.callable == "predict"
    assert result.manifest.model.framework == "python-callable"
    # The validation service analyzes an accepted package (Module 4): the
    # derived contract reflects the manifest it just validated.
    assert result.contract is not None
    assert result.contract.entrypoint_callable == "predict"
    assert result.contract.framework == "python-callable"
    assert result.contract.dependencies == ("numpy==2.1.0",)


def test_valid_package_with_verified_asset_is_accepted(validate: Validate) -> None:
    archive = _with_assets({"path": "assets/weights.bin", "sha256": WEIGHTS_SHA256})

    result = validate(archive)

    assert result.state is ValidationState.VALIDATED
    assert result.findings == ()


def test_findings_carry_a_stable_path(validate: Validate) -> None:
    result = validate(build_forge(manifest(dependencies=["numpy>=2.1.0"])))

    (finding,) = result.findings
    assert finding.code == Finding.DEPENDENCY_NOT_PINNED.value
    assert finding.path == ("dependencies", 0)


def test_validation_is_deterministic(validate: Validate) -> None:
    archive = build_forge(manifest(dependencies=["-e .", "numpy>=2"]))

    first = validate(archive)
    second = validate(archive)

    assert [(item.code, item.path) for item in first.findings] == [
        (item.code, item.path) for item in second.findings
    ]
