"""Validate a stored .forge artifact against the format version 1 contract."""

from __future__ import annotations

from forgeml.core.config import PackageLimits
from forgeml.domain.package.models import ArchiveUnreadable, PackageValidation
from forgeml.domain.package.ports import ArchiveReader, ArtifactStore
from forgeml.domain.package.rules import (
    asset_checksum_findings,
    rejected_with,
    unreadable_archive,
    validate_package,
)


class PackageValidationService:
    """Runs archive validation over a stored artifact.

    Asset checksums are the only rule that needs member bytes, so they are
    verified after the archive is known to be structurally safe and the
    manifest is known to be valid. Nothing before that point reads content.
    """

    def __init__(
        self,
        store: ArtifactStore,
        reader: ArchiveReader,
        limits: PackageLimits,
    ) -> None:
        self._store = store
        self._reader = reader
        self._limits = limits

    def validate(self, sha256: str) -> PackageValidation:
        with self._store.open(sha256) as stream:
            try:
                inspection = self._reader.inspect(stream, self._limits)
            except ArchiveUnreadable:
                return unreadable_archive()

            validation = validate_package(inspection, self._limits)
            if validation.manifest is None:
                return validation

            expected = {
                asset.path: asset.sha256
                for asset in validation.manifest.assets
                if asset.sha256 is not None
            }
            if not expected:
                return validation

            actual = self._reader.digest(stream, tuple(expected), self._limits)

        mismatched = asset_checksum_findings(expected, actual)
        if not mismatched:
            return validation
        return rejected_with(validation, mismatched)
