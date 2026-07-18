"""Startup recovery and the platform-failure path.

These are the paths that only run when something has already gone wrong, which
is exactly why they need tests: nobody exercises them by hand.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from forgeml.application.package.services import PackageService
from forgeml.core.config import PackageLimits, load_settings
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.operations.models import OperationState, OperationType
from forgeml.domain.package.ports import StoredArtifact
from forgeml.infrastructure.database.provider import DatabaseProvider
from forgeml.infrastructure.package.zip_archive import ZipArchiveReader
from forgeml.infrastructure.storage.artifact_store import FilesystemArtifactStore
from tests.integration.api.conftest import TABLES, database_url
from tests.packages import build_forge
from tests.support import TEST_PRINCIPAL

LIMITS = PackageLimits()


class VanishingArtifactStore:
    """Stores an archive, then loses it before anything can read it.

    A disk failure, an over-eager cleanup, or a restored backup all look like
    this. The platform must fail the operation, not report a package verdict it
    never actually reached.
    """

    def __init__(self, root: Path) -> None:
        self._real = FilesystemArtifactStore(root)

    def put(self, stream: BinaryIO, limits: PackageLimits) -> StoredArtifact:
        return self._real.put(stream, limits)

    def open(self, sha256: str) -> BinaryIO:
        raise AppError(
            category=ErrorCategory.NOT_FOUND,
            code="artifact_not_found",
            message="the referenced artifact does not exist",
        )

    def delete(self, sha256: str) -> None:  # pragma: no cover - unused here
        self._real.delete(sha256)


@pytest.fixture
def provider(migrated: None, tmp_path: Path) -> Iterator[DatabaseProvider]:
    engine = create_engine(database_url(), future=True)
    with engine.begin() as connection:
        connection.execute(
            text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
        )
    engine.dispose()

    settings = load_settings(
        {
            "FORGEML_ENVIRONMENT": "test",
            "FORGEML_DATABASE_URL": database_url(),
            "FORGEML_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
        }
    )
    created = DatabaseProvider(settings)
    yield created
    created.dispose()


def test_an_unreadable_artifact_fails_the_operation(
    provider: DatabaseProvider, tmp_path: Path
) -> None:
    service = PackageService(
        unit_of_work=provider.unit_of_work,
        store=VanishingArtifactStore(tmp_path / "artifacts"),
        reader=ZipArchiveReader(),
        limits=LIMITS,
    )

    operation = service.upload(
        stream=io.BytesIO(build_forge()),
        filename="model.forge",
        idempotency_key="key-1",
        correlation_id=uuid4(),
        principal=TEST_PRINCIPAL,
    )

    # The platform could not do the work, so the operation FAILED. It did not
    # "succeed" with a rejected package, which would blame the operator for an
    # infrastructure fault.
    assert operation.state is OperationState.FAILED
    assert operation.failure is not None
    assert operation.failure.code == "artifact_unreadable"


def test_startup_returns_an_abandoned_operation_to_the_queue(
    provider: DatabaseProvider,
) -> None:
    """ADR-016, end to end: a worker dies mid-operation and the platform heals."""

    with provider.unit_of_work() as uow:
        uow.operations.begin(
            idempotency_key="key-1",
            type=OperationType.PACKAGE_VALIDATE,
            target_id="a" * 64,
            request_fingerprint="fp",
            correlation_id=uuid4(),
        )
        claimed = uow.operations.claim_next()
        assert claimed is not None
        uow.commit()
    # The process now dies, leaving that operation RUNNING forever.

    recovered = provider.recover_orphaned_operations()

    assert recovered == 1
    with provider.unit_of_work() as uow:
        requeued = uow.operations.get(claimed.id)
    assert requeued is not None
    assert requeued.state is OperationState.PENDING


def test_startup_recovery_is_harmless_when_nothing_was_abandoned(
    provider: DatabaseProvider,
) -> None:
    assert provider.recover_orphaned_operations() == 0
