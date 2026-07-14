"""The Module 2 port contract, enforced against every implementation.

These are the laws Module 3 is allowed to rely on. They run against the
in-memory fakes and against real PostgreSQL, so a fake that quietly disagrees
with the database fails here rather than in production.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

from forgeml.application.unit_of_work import UnitOfWork
from forgeml.core.errors import AppError, ErrorCategory, ErrorDetail
from forgeml.domain.audit.models import ActorType, AuditEvent
from forgeml.domain.operations.models import (
    MAX_ATTEMPTS,
    OperationFailure,
    OperationState,
    OperationType,
)
from forgeml.domain.package.models import (
    ManifestV1,
    PackageState,
    PackageValidation,
    ValidationState,
)
from forgeml.infrastructure.database.engine import create_session_factory
from forgeml.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from tests.fakes import InMemoryUnitOfWork
from tests.packages import VALID_MANIFEST

DEFAULT_URL = "postgresql+psycopg://forgeml:forgeml@127.0.0.1:55432/forgeml"
TABLES = ("audit_events", "package_validations", "operations", "packages")
SHA = "a" * 64
OTHER_SHA = "b" * 64
VALIDATE = OperationType.PACKAGE_VALIDATE


@pytest.fixture(scope="session")
def postgres_engine() -> Iterator[Engine]:
    url = os.environ.get("FORGEML_TEST_DATABASE_URL", DEFAULT_URL)
    engine = create_engine(url, future=True)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture(params=["memory", "postgres"])
def uow(request: pytest.FixtureRequest) -> UnitOfWork:
    if request.param == "memory":
        return InMemoryUnitOfWork()

    engine = request.getfixturevalue("postgres_engine")
    with engine.begin() as connection:
        connection.execute(
            text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
        )
    return SqlAlchemyUnitOfWork(create_session_factory(engine))


def rejected() -> PackageValidation:
    return PackageValidation(
        state=ValidationState.REJECTED, validator_version="1", findings=()
    )


def validated() -> PackageValidation:
    return PackageValidation(
        state=ValidationState.VALIDATED, validator_version="1", findings=()
    )


def validated_with_manifest() -> PackageValidation:
    return PackageValidation(
        state=ValidationState.VALIDATED,
        validator_version="1",
        findings=(),
        manifest=ManifestV1.model_validate(VALID_MANIFEST),
    )


def with_findings() -> PackageValidation:
    return PackageValidation(
        state=ValidationState.REJECTED,
        validator_version="1",
        findings=(
            ErrorDetail(code="asset_missing", message="absent", path=("assets", 0)),
            ErrorDetail(code="schema_invalid", message="bad", path=None),
        ),
    )


# --------------------------------------------------------------------- packages


def test_a_stored_package_can_be_read_back_by_checksum(uow: UnitOfWork) -> None:
    with uow:
        created = uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
        uow.commit()

    with uow:
        found = uow.packages.find_by_checksum(SHA)
        by_id = uow.packages.find_by_id(created.id)

    assert found is not None and found.id == created.id
    assert by_id is not None and by_id.sha256 == SHA
    assert created.state is PackageState.DRAFT


def test_storing_the_same_checksum_twice_returns_one_package(uow: UnitOfWork) -> None:
    with uow:
        first = uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
        uow.commit()
    with uow:
        second = uow.packages.get_or_create(SHA, "other.forge", 99, f"artifact://{SHA}")
        uow.commit()

    assert first.id == second.id
    assert second.filename == "m.forge"  # the first record wins; it is immutable


def test_validation_transitions_the_package_and_is_readable(uow: UnitOfWork) -> None:
    with uow:
        package = uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
        uow.packages.save_validation(package.id, validated())
        uow.commit()

    with uow:
        stored = uow.packages.find_by_id(package.id)
        history = uow.packages.findings_for(package.id)

    assert stored is not None
    assert stored.state is PackageState.VALIDATED
    assert [item.state for item in history] == [ValidationState.VALIDATED]


def test_rejected_validation_transitions_the_package_to_rejected(
    uow: UnitOfWork,
) -> None:
    with uow:
        package = uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
        uow.packages.save_validation(package.id, rejected())
        uow.commit()

    with uow:
        stored = uow.packages.find_by_id(package.id)

    assert stored is not None and stored.state is PackageState.REJECTED


def test_revalidating_with_the_same_validator_is_idempotent(uow: UnitOfWork) -> None:
    with uow:
        package = uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
        uow.packages.save_validation(package.id, rejected())
        uow.packages.save_validation(package.id, validated())
        uow.commit()

    with uow:
        history = uow.packages.findings_for(package.id)
        stored = uow.packages.find_by_id(package.id)

    assert len(history) == 1
    assert stored is not None and stored.state is PackageState.VALIDATED


def test_a_draft_package_claims_no_manifest_version(uow: UnitOfWork) -> None:
    # Nothing has parsed the archive yet. Recording a format version here would
    # be a fabricated fact in a durable record.
    with uow:
        package = uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
        uow.commit()

    assert package.manifest_version is None

    with uow:
        uow.packages.save_validation(package.id, validated_with_manifest())
        uow.commit()

    with uow:
        stored = uow.packages.find_by_id(package.id)

    assert stored is not None
    assert stored.manifest_version == 1
    assert stored.manifest is not None
    assert stored.manifest.entrypoint.callable == "predict"


def test_validating_an_absent_package_is_not_found(uow: UnitOfWork) -> None:
    with uow, pytest.raises(AppError) as captured:
        uow.packages.save_validation(uuid4(), validated())

    assert captured.value.category is ErrorCategory.NOT_FOUND


def test_findings_survive_persistence_in_order_and_with_their_paths(
    uow: UnitOfWork,
) -> None:
    # Docs 12 renders these as error-envelope details. A dropped path or a
    # reordered list is a silent contract break no constraint would catch.
    with uow:
        package = uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
        uow.packages.save_validation(package.id, with_findings())
        uow.commit()

    with uow:
        (stored,) = uow.packages.findings_for(package.id)

    assert [item.code for item in stored.findings] == [
        "asset_missing",
        "schema_invalid",
    ]
    assert stored.findings[0].path == ("assets", 0)
    assert stored.findings[1].path is None


def test_a_read_audit_event_carries_its_identity_and_time(uow: UnitOfWork) -> None:
    with uow:
        uow.audit.record(
            AuditEvent(
                actor_type=ActorType.SYSTEM,
                action="package.created",
                target_type="package",
                target_id=SHA,
                correlation_id=uuid4(),
            )
        )
        uow.commit()

    with uow:
        (stored,) = uow.audit.for_target(SHA, limit=10)

    assert stored.id is not None
    assert stored.occurred_at is not None


def test_a_returned_operation_result_cannot_mutate_stored_state(
    uow: UnitOfWork,
) -> None:
    with uow:
        uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        claimed = uow.operations.claim_next()
        assert claimed is not None
        done = uow.operations.complete(claimed.id, {"package_id": "abc"})
        uow.commit()

    assert done.result is not None
    done.result["package_id"] = "tampered"

    with uow:
        stored = uow.operations.get(done.id)

    assert stored is not None and stored.result == {"package_id": "abc"}


def test_packages_are_listed_newest_first_and_paginate(uow: UnitOfWork) -> None:
    with uow:
        for index in range(3):
            uow.packages.get_or_create(
                f"{index}" * 64, f"m{index}.forge", 10, f"artifact://{index}"
            )
        uow.commit()

    with uow:
        first = uow.packages.list(limit=2)
        second = uow.packages.list(limit=2, cursor=first.next_cursor)

    assert len(first.items) == 2
    assert first.next_cursor is not None
    assert len(second.items) == 1
    assert second.next_cursor is None
    identifiers = [item.id for item in (*first.items, *second.items)]
    assert len(set(identifiers)) == 3  # no row is skipped or repeated across pages


def test_an_invalid_cursor_is_a_bad_request(uow: UnitOfWork) -> None:
    with uow, pytest.raises(AppError) as captured:
        uow.packages.list(limit=2, cursor="not-a-cursor")

    assert captured.value.code == "cursor_invalid"


# ------------------------------------------------------------------- operations


def test_the_same_key_and_fingerprint_returns_the_original_operation(
    uow: UnitOfWork,
) -> None:
    with uow:
        first = uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        uow.commit()
    with uow:
        second = uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        uow.commit()

    assert first.id == second.id
    assert second.state is OperationState.PENDING


def test_the_same_key_with_a_different_fingerprint_conflicts(uow: UnitOfWork) -> None:
    with uow:
        uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        uow.commit()

    with uow, pytest.raises(AppError) as captured:
        uow.operations.begin("key-1", VALIDATE, SHA, "different", uuid4())

    assert captured.value.category is ErrorCategory.CONFLICT
    assert captured.value.code == "idempotency_conflict"


def test_the_same_key_against_a_different_target_is_a_different_operation(
    uow: UnitOfWork,
) -> None:
    with uow:
        first = uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        second = uow.operations.begin("key-1", VALIDATE, OTHER_SHA, "fp", uuid4())
        uow.commit()

    assert first.id != second.id


def test_claiming_takes_the_oldest_pending_operation_once(uow: UnitOfWork) -> None:
    with uow:
        first = uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        uow.operations.begin("key-2", VALIDATE, OTHER_SHA, "fp", uuid4())
        uow.commit()

    with uow:
        claimed = uow.operations.claim_next()
        uow.commit()

    assert claimed is not None
    assert claimed.id == first.id
    assert claimed.state is OperationState.RUNNING
    assert claimed.attempts == 1


def test_claiming_an_empty_queue_returns_nothing(uow: UnitOfWork) -> None:
    with uow:
        assert uow.operations.claim_next() is None


def test_a_lane_never_claims_another_lanes_work(uow: UnitOfWork) -> None:
    # Only one operation type exists today, so the negative case is what can be
    # asserted: an empty lane must not fall through to another lane's work.
    with uow:
        uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        uow.commit()

    with uow:
        claimed = uow.operations.claim_next(types=())

    assert claimed is None


def test_a_completed_operation_is_terminal_and_immutable(uow: UnitOfWork) -> None:
    with uow:
        uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        claimed = uow.operations.claim_next()
        assert claimed is not None
        done = uow.operations.complete(claimed.id, {"package_id": str(uuid4())})
        uow.commit()

    assert done.state is OperationState.SUCCEEDED
    assert done.completed_at is not None

    with uow, pytest.raises(AppError) as captured:
        uow.operations.complete(done.id, {"changed": "answer"})

    assert captured.value.code == "invalid_state_transition"


def test_a_failed_operation_records_a_safe_failure(uow: UnitOfWork) -> None:
    with uow:
        uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        claimed = uow.operations.claim_next()
        assert claimed is not None
        failed = uow.operations.fail(
            claimed.id, OperationFailure("package_invalid", "the package was rejected")
        )
        uow.commit()

    assert failed.state is OperationState.FAILED
    assert failed.failure is not None
    assert failed.failure.code == "package_invalid"


def test_completing_an_unclaimed_operation_is_rejected(uow: UnitOfWork) -> None:
    with uow:
        pending = uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        uow.commit()

    with uow, pytest.raises(AppError) as captured:
        uow.operations.complete(pending.id, {})

    assert captured.value.code == "invalid_state_transition"


def test_completing_an_absent_operation_is_not_found(uow: UnitOfWork) -> None:
    with uow, pytest.raises(AppError) as captured:
        uow.operations.complete(uuid4(), {})

    assert captured.value.category is ErrorCategory.NOT_FOUND


def test_an_operation_orphaned_by_a_dead_worker_returns_to_the_queue(
    uow: UnitOfWork,
) -> None:
    # ADR-016: without recovery this row stays RUNNING forever and the client
    # polls an operation that can never terminate.
    with uow:
        uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        claimed = uow.operations.claim_next()
        assert claimed is not None
        uow.commit()

    with uow:
        recovered = uow.operations.recover_orphaned()
        uow.commit()

    with uow:
        requeued = uow.operations.claim_next()
        uow.commit()

    assert recovered == 1
    assert requeued is not None
    assert requeued.id == claimed.id
    assert requeued.attempts == 2


def test_an_operation_that_exhausts_its_attempts_is_abandoned(uow: UnitOfWork) -> None:
    with uow:
        started = uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        uow.commit()

    for _ in range(MAX_ATTEMPTS):
        with uow:
            uow.operations.claim_next()
            uow.commit()
        with uow:
            uow.operations.recover_orphaned()
            uow.commit()

    with uow:
        final = uow.operations.get(started.id)

    assert final is not None
    assert final.state is OperationState.FAILED
    assert final.failure is not None
    assert final.failure.code == "operation_abandoned"


def test_recovery_leaves_terminal_operations_alone(uow: UnitOfWork) -> None:
    with uow:
        uow.operations.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        claimed = uow.operations.claim_next()
        assert claimed is not None
        uow.operations.complete(claimed.id, {})
        uow.commit()

    with uow:
        recovered = uow.operations.recover_orphaned()
        uow.commit()

    with uow:
        stored = uow.operations.get(claimed.id)

    assert recovered == 0
    assert stored is not None and stored.state is OperationState.SUCCEEDED


# ------------------------------------------------------------------------ audit


def test_an_audit_event_is_readable_by_target_and_correlation(uow: UnitOfWork) -> None:
    correlation = uuid4()
    with uow:
        uow.audit.record(
            AuditEvent(
                actor_type=ActorType.OPERATOR,
                action="package.validated",
                target_type="package",
                target_id=SHA,
                correlation_id=correlation,
                metadata={"state": "validated"},
            )
        )
        uow.commit()

    with uow:
        by_target = uow.audit.for_target(SHA, limit=10)
        by_correlation = uow.audit.for_correlation(correlation)

    assert [item.action for item in by_target] == ["package.validated"]
    assert [item.action for item in by_correlation] == ["package.validated"]
    assert by_target[0].metadata == {"state": "validated"}


# ----------------------------------------------------------------- transactions


def test_an_exception_mid_transaction_leaves_nothing_behind(uow: UnitOfWork) -> None:
    # The audit record and the state change it describes must be one transaction
    # (docs 04). If either can survive alone, the audit trail is fiction.
    with pytest.raises(RuntimeError, match="boom"), uow:
        package = uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
        uow.packages.save_validation(package.id, validated())
        uow.audit.record(
            AuditEvent(
                actor_type=ActorType.SYSTEM,
                action="package.validated",
                target_type="package",
                target_id=SHA,
                correlation_id=uuid4(),
            )
        )
        raise RuntimeError("boom")

    with uow:
        assert uow.packages.find_by_checksum(SHA) is None
        assert uow.audit.for_target(SHA, limit=10) == []


def test_leaving_the_unit_of_work_without_committing_persists_nothing(
    uow: UnitOfWork,
) -> None:
    with uow:
        uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")

    with uow:
        assert uow.packages.find_by_checksum(SHA) is None


def test_an_explicit_rollback_discards_writes(uow: UnitOfWork) -> None:
    with uow:
        uow.packages.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
        uow.rollback()
        uow.commit()

    with uow:
        assert uow.packages.find_by_checksum(SHA) is None
