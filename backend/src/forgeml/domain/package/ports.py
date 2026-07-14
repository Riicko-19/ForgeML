"""Ports owned by the package domain.

Callers never receive a filesystem path. An artifact is addressed by its
SHA-256 (ADR-003) and referenced by an opaque URI, so a later object-storage
adapter changes nothing above this line.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import BinaryIO, Protocol

from forgeml.core.config import PackageLimits
from forgeml.domain.package.models import ArchiveInspection


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    """An immutable, content-addressed archive held by the artifact store."""

    sha256: str
    size_bytes: int
    uri: str


class ArtifactStore(Protocol):
    """Streaming, content-addressed, atomically written artifact storage."""

    def put(self, stream: BinaryIO, limits: PackageLimits) -> StoredArtifact:
        """Store the stream, returning its identity. Writing the same bytes twice
        is idempotent, and a failed write leaves no artifact behind."""

    def open(self, sha256: str) -> BinaryIO:
        """Open a stored artifact for reading."""

    def delete(self, sha256: str) -> None:
        """Delete a stored artifact. Deleting an absent artifact is not an error."""


class ArchiveReader(Protocol):
    """Reads .forge archive structure without importing or executing its content."""

    def inspect(self, stream: BinaryIO, limits: PackageLimits) -> ArchiveInspection:
        """Read member headers and the manifest document.

        Raises ArchiveUnreadable when the bytes are not a readable ZIP container.
        """

    def digest(
        self, stream: BinaryIO, paths: tuple[str, ...], limits: PackageLimits
    ) -> Mapping[str, str]:
        """Compute the SHA-256 of the named members, reading bounded bytes only."""

    def extract(
        self, stream: BinaryIO, destination: str, limits: PackageLimits
    ) -> None:
        """Extract the archive into a fresh, empty staging directory."""
