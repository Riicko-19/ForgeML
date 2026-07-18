"""Ports owned by the package domain.

Callers never receive a filesystem path. An artifact is addressed by its
SHA-256 (ADR-003) and referenced by an opaque URI, so a later object-storage
adapter changes nothing above this line.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import BinaryIO, Protocol
from uuid import UUID

from forgeml.core.config import PackageLimits
from forgeml.domain.package.models import (
    ArchiveInspection,
    Package,
    PackageValidation,
)


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
        """Delete a stored artifact. Deleting an absent artifact is not an error.

        Nothing calls this yet. It is the primitive ADR-012's retention and
        disk-pressure policy needs, and that policy belongs to Module 10 --
        artifacts currently accumulate without bound.
        """


@dataclass(frozen=True, slots=True)
class PackagePage:
    """One page of packages, newest first."""

    items: tuple[Package, ...]
    next_cursor: str | None


class PackageCatalog(Protocol):
    """Durable package records. Duplicate checksums resolve to one package."""

    def get_or_create(
        self, sha256: str, filename: str, size_bytes: int, artifact_uri: str
    ) -> Package:
        """Return the package for these bytes, creating it in DRAFT if absent.

        Storing the same archive twice is idempotent (ADR-003): the second call
        returns the first package unchanged, and never a second record.
        """

    def find_by_id(self, package_id: UUID) -> Package | None:
        """Read one package by its opaque identifier."""

    def find_by_checksum(self, sha256: str) -> Package | None:
        """Read one package by the SHA-256 of its bytes."""

    def save_validation(self, package_id: UUID, validation: PackageValidation) -> None:
        """Persist a validation result and transition the package accordingly.

        Raises AppError(NOT_FOUND) when the package does not exist.
        """

    def list(self, limit: int, cursor: str | None = None) -> PackagePage:
        """List packages newest first, bounded by limit."""

    def findings_for(self, package_id: UUID) -> Sequence[PackageValidation]:
        """Read the validation history of one package, newest first."""


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
