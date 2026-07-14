"""ZIP reader against real archives, including safe extraction."""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from forgeml.core.config import PackageLimits
from forgeml.core.errors import AppError
from forgeml.domain.package.models import ArchiveUnreadable, Finding
from forgeml.infrastructure.package.zip_archive import ZipArchiveReader
from tests.packages import DEFAULT_FILES, ENTRYPOINT_SOURCE, build_forge, symlink_member

LIMITS = PackageLimits()
WEIGHTS = b"reference weights"


@pytest.fixture
def reader() -> ZipArchiveReader:
    return ZipArchiveReader()


def stream(archive: bytes) -> io.BytesIO:
    return io.BytesIO(archive)


def test_inspect_reads_headers_and_manifest(reader: ZipArchiveReader) -> None:
    inspection = reader.inspect(stream(build_forge()), LIMITS)

    names = {entry.name for entry in inspection.entries}
    assert names == {"forge.yaml", "src/model.py"}
    assert inspection.manifest_fault is None
    assert inspection.manifest_document is not None
    assert inspection.manifest_document["forge_version"] == 1


def test_bytes_that_are_not_a_zip_container_are_unreadable(
    reader: ZipArchiveReader,
) -> None:
    with pytest.raises(ArchiveUnreadable):
        reader.inspect(stream(b"definitely not a zip"), LIMITS)


def test_symlink_member_is_reported_as_a_symlink(reader: ZipArchiveReader) -> None:
    archive = build_forge(hostile=[symlink_member("src/link.py", "/etc/passwd")])

    inspection = reader.inspect(stream(archive), LIMITS)

    link = next(item for item in inspection.entries if item.name == "src/link.py")
    assert link.is_symlink
    assert not link.is_regular_file


def test_oversized_manifest_is_not_read_into_memory(reader: ZipArchiveReader) -> None:
    limits = PackageLimits(max_manifest_bytes=64)
    archive = build_forge(raw_manifest=b"# padding\n" * 100)

    inspection = reader.inspect(stream(archive), limits)

    assert inspection.manifest_document is None
    assert inspection.manifest_fault is Finding.MANIFEST_TOO_LARGE


def test_manifest_that_is_not_utf8_is_malformed(reader: ZipArchiveReader) -> None:
    inspection = reader.inspect(
        stream(build_forge(raw_manifest=b"\xff\xfe\x00")), LIMITS
    )

    assert inspection.manifest_fault is Finding.MANIFEST_MALFORMED


def test_a_directory_named_forge_yaml_is_not_a_manifest(
    reader: ZipArchiveReader,
) -> None:
    archive = build_forge(
        include_manifest=False,
        hostile=[(zipfile.ZipInfo("forge.yaml/"), b"")],
    )

    inspection = reader.inspect(stream(archive), LIMITS)

    assert inspection.manifest_fault is Finding.MANIFEST_MISSING


def test_digest_matches_the_member_content(reader: ZipArchiveReader) -> None:
    archive = build_forge(files={**DEFAULT_FILES, "assets/weights.bin": WEIGHTS})

    digests = reader.digest(stream(archive), ("assets/weights.bin",), LIMITS)

    assert digests["assets/weights.bin"] == hashlib.sha256(WEIGHTS).hexdigest()


def test_digest_of_an_absent_member_is_simply_absent(reader: ZipArchiveReader) -> None:
    digests = reader.digest(stream(build_forge()), ("assets/absent.bin",), LIMITS)

    assert digests == {}


def test_digest_ignores_a_directory_member(reader: ZipArchiveReader) -> None:
    archive = build_forge(hostile=[(zipfile.ZipInfo("assets/"), b"")])

    digests = reader.digest(stream(archive), ("assets/",), LIMITS)

    assert digests == {}


def test_extract_recreates_directory_members(
    reader: ZipArchiveReader, tmp_path: Path
) -> None:
    archive = build_forge(hostile=[(zipfile.ZipInfo("assets/"), b"")])

    reader.extract(stream(archive), str(tmp_path), LIMITS)

    assert (tmp_path / "assets").is_dir()


def test_extract_writes_the_archive_into_staging(
    reader: ZipArchiveReader, tmp_path: Path
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()

    reader.extract(stream(build_forge()), str(staging), LIMITS)

    assert (staging / "src" / "model.py").read_bytes() == ENTRYPOINT_SOURCE
    assert (staging / "forge.yaml").is_file()


def test_extract_refuses_a_symlink_member(
    reader: ZipArchiveReader, tmp_path: Path
) -> None:
    archive = build_forge(hostile=[symlink_member("src/link.py", "/etc/passwd")])

    with pytest.raises(AppError, match=r"not safe to extract"):
        reader.extract(stream(archive), str(tmp_path), LIMITS)

    assert not (tmp_path / "src" / "link.py").exists()


def test_extract_refuses_to_escape_the_destination(
    reader: ZipArchiveReader, tmp_path: Path
) -> None:
    archive = build_forge(hostile=[(zipfile.ZipInfo("../escape.py"), b"x")])
    destination = tmp_path / "staging"
    destination.mkdir()

    with pytest.raises(AppError):
        reader.extract(stream(archive), str(destination), LIMITS)

    assert not (tmp_path / "escape.py").exists()


def test_extract_stops_at_the_expansion_limit(
    reader: ZipArchiveReader, tmp_path: Path
) -> None:
    limits = PackageLimits(
        max_uncompressed_bytes=1_024,
        max_archive_bytes=1_024,
        max_manifest_bytes=1_024,
    )
    archive = build_forge(files={"src/model.py": b"x" * 4_096})

    with pytest.raises(AppError):
        reader.extract(stream(archive), str(tmp_path), limits)
