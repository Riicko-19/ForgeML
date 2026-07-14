"""Validation policy over header-level facts, with no archive present."""

from __future__ import annotations

import dataclasses

import pytest

from forgeml.core.config import PackageLimits
from forgeml.domain.package.models import (
    ArchiveEntry,
    ArchiveInspection,
    Finding,
    ValidationState,
)
from forgeml.domain.package.rules import (
    MAX_FINDINGS,
    asset_checksum_findings,
    unreadable_archive,
    validate_package,
)

LIMITS = PackageLimits()


def entry(name: str, **overrides: object) -> ArchiveEntry:
    base = ArchiveEntry(
        name=name,
        is_directory=name.endswith("/"),
        is_regular_file=not name.endswith("/"),
        is_symlink=False,
        is_encrypted=False,
        has_utf8_name=True,
        compressed_size=64,
        uncompressed_size=128,
    )
    return dataclasses.replace(base, **overrides)  # type: ignore[arg-type]


def codes(*entries: ArchiveEntry, limits: PackageLimits = LIMITS) -> set[str]:
    result = validate_package(ArchiveInspection(entries=entries), limits)
    assert result.state is ValidationState.REJECTED
    return {finding.code for finding in result.findings}


def test_entry_limit_short_circuits_before_any_other_rule() -> None:
    limits = PackageLimits(max_entries=2)
    entries = tuple(entry(f"src/m{index}.py") for index in range(3))

    result = validate_package(ArchiveInspection(entries=entries), limits)

    assert [finding.code for finding in result.findings] == [
        Finding.ARCHIVE_ENTRY_LIMIT_EXCEEDED.value
    ]


def test_total_expansion_beyond_policy_is_rejected() -> None:
    limits = PackageLimits(
        max_uncompressed_bytes=1_024,
        max_archive_bytes=1_024,
        max_manifest_bytes=1_024,
    )
    big = entry("src/model.py", uncompressed_size=2_048, compressed_size=2_048)

    assert Finding.ARCHIVE_UNCOMPRESSED_LIMIT_EXCEEDED.value in codes(
        big, limits=limits
    )


def test_small_highly_compressible_member_is_not_a_bomb() -> None:
    # Below the ratio floor the rule must stay silent, or every tiny text file
    # in a normal package would be reported as a zip bomb.
    tiny = entry("src/model.py", uncompressed_size=4_096, compressed_size=8)

    result = validate_package(ArchiveInspection(entries=(tiny,)), LIMITS)

    assert Finding.ARCHIVE_COMPRESSION_RATIO_EXCEEDED.value not in {
        finding.code for finding in result.findings
    }


def test_member_that_is_neither_file_nor_directory_is_rejected() -> None:
    device = entry("src/device", is_regular_file=False)

    assert Finding.ARCHIVE_UNSUPPORTED_MEMBER_TYPE.value in codes(device)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("src/../../etc/passwd", Finding.ARCHIVE_PATH_TRAVERSAL),
        ("C:/windows/system32", Finding.ARCHIVE_PATH_ABSOLUTE),
        ("src\\model.py", Finding.ARCHIVE_PATH_NOT_NORMALIZED),
        ("src//model.py", Finding.ARCHIVE_PATH_NOT_NORMALIZED),
        ("src/./model.py", Finding.ARCHIVE_PATH_NOT_NORMALIZED),
    ],
)
def test_unsafe_member_paths_are_rejected(name: str, expected: Finding) -> None:
    assert expected.value in codes(entry("src/model.py"), entry(name))


def test_hostile_member_name_cannot_break_the_error_contract() -> None:
    # A finding path segment is bounded and control-character free, so a
    # hostile name cannot make the validator raise while reporting it.
    hostile = entry("src/" + "\x00nasty" * 200)

    result = validate_package(ArchiveInspection(entries=(hostile,)), LIMITS)

    for finding in result.findings:
        assert finding.path is None or all(
            len(str(segment)) <= 128 for segment in finding.path
        )


def test_findings_are_truncated_to_a_bounded_report() -> None:
    entries = tuple(
        entry(f"src/bad{index}.py", is_symlink=True)
        for index in range(MAX_FINDINGS + 5)
    )

    result = validate_package(ArchiveInspection(entries=entries), LIMITS)

    assert len(result.findings) == MAX_FINDINGS + 1
    assert result.findings[-1].code == Finding.FINDINGS_TRUNCATED.value


def test_unreadable_archive_reports_one_stable_finding() -> None:
    result = unreadable_archive()

    assert result.state is ValidationState.REJECTED
    assert [finding.code for finding in result.findings] == [
        Finding.ARCHIVE_UNREADABLE.value
    ]


def test_missing_manifest_document_without_fault_defaults_to_missing() -> None:
    inspection = ArchiveInspection(entries=(entry("src/model.py"),))

    result = validate_package(inspection, LIMITS)

    assert [finding.code for finding in result.findings] == [
        Finding.MANIFEST_MISSING.value
    ]


def test_asset_checksum_findings_report_absent_and_mismatched_assets() -> None:
    findings = asset_checksum_findings(
        {"a.bin": "0" * 64, "b.bin": "1" * 64},
        {"b.bin": "1" * 64},
    )

    assert [finding.code for finding in findings] == [
        Finding.ASSET_CHECKSUM_MISMATCH.value
    ]
    assert findings[0].path == ("assets", "a.bin")
