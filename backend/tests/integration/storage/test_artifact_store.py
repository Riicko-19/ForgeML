"""Filesystem artifact store against a real directory."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from forgeml.core.config import PackageLimits
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.infrastructure.storage.artifact_store import (
    FilesystemArtifactStore,
    artifact_uri,
)

LIMITS = PackageLimits()
PAYLOAD = b"forge archive bytes"
PAYLOAD_SHA256 = hashlib.sha256(PAYLOAD).hexdigest()


@pytest.fixture
def store(tmp_path: Path) -> FilesystemArtifactStore:
    return FilesystemArtifactStore(tmp_path)


def test_artifact_is_addressed_by_its_own_checksum(
    store: FilesystemArtifactStore,
) -> None:
    stored = store.put(io.BytesIO(PAYLOAD), LIMITS)

    assert stored.sha256 == PAYLOAD_SHA256
    assert stored.size_bytes == len(PAYLOAD)
    assert stored.uri == artifact_uri(PAYLOAD_SHA256)
    with store.open(stored.sha256) as stream:
        assert stream.read() == PAYLOAD


def test_storing_the_same_bytes_twice_is_idempotent(
    store: FilesystemArtifactStore, tmp_path: Path
) -> None:
    first = store.put(io.BytesIO(PAYLOAD), LIMITS)
    second = store.put(io.BytesIO(PAYLOAD), LIMITS)

    assert first == second
    assert len(list(tmp_path.rglob(PAYLOAD_SHA256))) == 1


def test_oversized_upload_is_rejected_and_leaves_no_artifact(
    store: FilesystemArtifactStore, tmp_path: Path
) -> None:
    limits = PackageLimits(
        max_archive_bytes=1_024,
        max_uncompressed_bytes=1_024,
        max_manifest_bytes=1_024,
    )

    with pytest.raises(AppError) as captured:
        store.put(io.BytesIO(b"x" * 2_048), limits)

    assert captured.value.category is ErrorCategory.VALIDATION
    assert captured.value.code == "archive_too_large"
    assert not list((tmp_path / ".staging").iterdir())


def test_failed_write_leaves_no_staging_residue(
    store: FilesystemArtifactStore, tmp_path: Path
) -> None:
    class Failing(io.RawIOBase):
        def read(self, size: int = -1) -> bytes:
            raise OSError("disk went away")

    with pytest.raises(OSError, match="disk went away"):
        store.put(Failing(), LIMITS)  # type: ignore[arg-type]

    assert not list((tmp_path / ".staging").iterdir())


def test_reading_an_absent_artifact_is_a_not_found_error(
    store: FilesystemArtifactStore,
) -> None:
    with pytest.raises(AppError) as captured:
        store.open("a" * 64)

    assert captured.value.category is ErrorCategory.NOT_FOUND
    assert captured.value.code == "artifact_not_found"


@pytest.mark.parametrize(
    "reference",
    ["../../etc/passwd", "not-hex", "", "A" * 64, "a" * 63],
)
def test_an_artifact_reference_that_is_not_a_digest_is_refused(
    store: FilesystemArtifactStore, reference: str
) -> None:
    with pytest.raises(AppError) as captured:
        store.open(reference)

    assert captured.value.code == "artifact_reference_invalid"


def test_delete_removes_the_artifact_and_tolerates_absence(
    store: FilesystemArtifactStore,
) -> None:
    stored = store.put(io.BytesIO(PAYLOAD), LIMITS)

    store.delete(stored.sha256)
    store.delete(stored.sha256)

    with pytest.raises(AppError):
        store.open(stored.sha256)
