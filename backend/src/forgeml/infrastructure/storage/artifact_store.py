"""Content-addressed artifact storage on a local filesystem (ADR-007, ADR-009)."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO

from forgeml.core.config import PackageLimits
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.package.models import Finding
from forgeml.domain.package.ports import StoredArtifact

_CHUNK_BYTES = 1_048_576
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STAGING = ".staging"
_ARTIFACT_MODE = 0o440


def artifact_uri(sha256: str) -> str:
    """The opaque reference callers hold instead of a filesystem path."""

    return f"artifact://{sha256}"


class FilesystemArtifactStore:
    """Streams archives to disk under their own SHA-256, atomically.

    A partial write never becomes an artifact: bytes land in a staging file
    that is either renamed into place once complete or removed.
    """

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._staging = self._root / _STAGING

    def put(self, stream: BinaryIO, limits: PackageLimits) -> StoredArtifact:
        self._staging.mkdir(parents=True, exist_ok=True)
        handle, name = tempfile.mkstemp(dir=self._staging)
        staged = Path(name)
        try:
            hasher = hashlib.sha256()
            size = 0
            with os.fdopen(handle, "wb") as sink:
                while chunk := stream.read(_CHUNK_BYTES):
                    size += len(chunk)
                    if size > limits.max_archive_bytes:
                        raise AppError(
                            category=ErrorCategory.VALIDATION,
                            code=Finding.ARCHIVE_TOO_LARGE.value,
                            message="package archive exceeds the allowed size",
                        )
                    hasher.update(chunk)
                    sink.write(chunk)
                sink.flush()
                os.fsync(sink.fileno())

            sha256 = hasher.hexdigest()
            final = self._locate(sha256)
            if final.exists():
                return StoredArtifact(sha256, size, artifact_uri(sha256))

            final.parent.mkdir(parents=True, exist_ok=True)
            staged.chmod(_ARTIFACT_MODE)
            os.replace(staged, final)
            self._fsync_directory(final.parent)
            return StoredArtifact(sha256, size, artifact_uri(sha256))
        finally:
            staged.unlink(missing_ok=True)

    def open(self, sha256: str) -> BinaryIO:
        try:
            return self._locate(sha256).open("rb")
        except FileNotFoundError as error:
            raise AppError(
                category=ErrorCategory.NOT_FOUND,
                code="artifact_not_found",
                message="the referenced artifact does not exist",
            ) from error

    def delete(self, sha256: str) -> None:
        self._locate(sha256).unlink(missing_ok=True)

    def _locate(self, sha256: str) -> Path:
        if not _SHA256.fullmatch(sha256):
            raise AppError(
                category=ErrorCategory.BAD_REQUEST,
                code="artifact_reference_invalid",
                message="an artifact reference must be a lower-case SHA-256 digest",
            )
        return self._root / sha256[:2] / sha256[2:4] / sha256

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
