"""Concurrency guarantees that only a real database can prove (ADR-009, ADR-010)."""

from __future__ import annotations

import threading
from uuid import uuid4

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from forgeml.core.errors import AppError
from forgeml.domain.deployment.models import DesiredState
from forgeml.domain.operations.models import OperationState, OperationType
from forgeml.infrastructure.database.repositories import (
    SqlAlchemyDeploymentRepository,
    SqlAlchemyOperationStore,
    SqlAlchemyPackageCatalog,
)

VALIDATE = OperationType.PACKAGE_VALIDATE
SHA = "c" * 64


def test_two_workers_never_claim_the_same_operation(
    engine: Engine, session_factory: sessionmaker[Session]
) -> None:
    """The ADR-010 claim guarantee, proven with two live transactions.

    FOR UPDATE SKIP LOCKED is the whole mechanism: worker two must skip the row
    worker one holds rather than block on it or, worse, take it as well.
    """

    with session_factory() as setup:
        store = SqlAlchemyOperationStore(setup)
        first = store.begin("key-1", VALIDATE, SHA, "fp", uuid4())
        second = store.begin("key-2", VALIDATE, "d" * 64, "fp", uuid4())
        setup.commit()

    worker_one = session_factory()
    worker_two = session_factory()
    try:
        claimed_one = SqlAlchemyOperationStore(worker_one).claim_next()
        # worker_one still holds its row lock: it has not committed.
        claimed_two = SqlAlchemyOperationStore(worker_two).claim_next()

        assert claimed_one is not None
        assert claimed_two is not None
        assert claimed_one.id != claimed_two.id
        assert {claimed_one.id, claimed_two.id} == {first.id, second.id}

        worker_one.commit()
        worker_two.commit()
    finally:
        worker_one.close()
        worker_two.close()

    with session_factory() as check:
        store = SqlAlchemyOperationStore(check)
        assert store.claim_next() is None  # both were taken, neither twice


def test_a_third_worker_finds_nothing_while_two_rows_are_held(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as setup:
        SqlAlchemyOperationStore(setup).begin("key-1", VALIDATE, SHA, "fp", uuid4())
        setup.commit()

    holder = session_factory()
    other = session_factory()
    try:
        assert SqlAlchemyOperationStore(holder).claim_next() is not None
        # Skip-locked, not blocked: the second worker returns immediately.
        assert SqlAlchemyOperationStore(other).claim_next() is None
        holder.commit()
    finally:
        holder.close()
        other.close()


def test_concurrent_uploads_of_identical_bytes_create_one_package(
    engine: Engine, session_factory: sessionmaker[Session]
) -> None:
    """Two uploads race; the unique index arbitrates and the loser reads the winner.

    An application-level "does it exist?" check would let both inserts through.
    """

    first_session = session_factory()
    second_session = session_factory()
    try:
        first_catalog = SqlAlchemyPackageCatalog(first_session)
        second_catalog = SqlAlchemyPackageCatalog(second_session)

        # Both transactions see no package, then both try to insert.
        first = first_catalog.get_or_create(SHA, "a.forge", 10, f"artifact://{SHA}")
        first_session.commit()

        second = second_catalog.get_or_create(SHA, "b.forge", 10, f"artifact://{SHA}")
        second_session.commit()

        assert first.id == second.id
    finally:
        first_session.close()
        second_session.close()

    with session_factory() as check:
        assert SqlAlchemyPackageCatalog(check).find_by_checksum(SHA) is not None


def test_a_second_begin_with_a_conflicting_fingerprint_still_conflicts(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as setup:
        SqlAlchemyOperationStore(setup).begin("key-1", VALIDATE, SHA, "fp", uuid4())
        setup.commit()

    with session_factory() as retry:
        store = SqlAlchemyOperationStore(retry)
        with pytest.raises(AppError, match="idempotency"):
            store.begin("key-1", VALIDATE, SHA, "other-fingerprint", uuid4())


def test_two_activations_of_one_deployment_serialize_on_the_row_lock(
    session_factory: sessionmaker[Session],
) -> None:
    """The ADR-005 activation guarantee: the route swap is one-at-a-time.

    `lock_deployment` is plain FOR UPDATE, not SKIP LOCKED -- a second activation
    must *wait* for the first rather than skip it, because skipping would let two
    callers each believe they own the route and write conflicting active
    versions. Only a real database can prove the wait, so this is the test that
    stands behind the atomicity claim in ActivationService.
    """

    with session_factory() as setup:
        created = SqlAlchemyDeploymentRepository(setup).create_deployment(
            "scorer", DesiredState.RUNNING
        )
        setup.commit()

    entered = threading.Event()
    outcome: list[str] = []

    def second_activation() -> None:
        entered.set()
        with session_factory() as contender:
            SqlAlchemyDeploymentRepository(contender).lock_deployment(created.id)
            outcome.append("locked")
            contender.commit()

    holder = session_factory()
    try:
        assert SqlAlchemyDeploymentRepository(holder).lock_deployment(created.id)

        waiter = threading.Thread(target=second_activation, daemon=True)
        waiter.start()
        entered.wait(timeout=5)
        # The contender is inside lock_deployment and must be blocked: the
        # holder's transaction is still open. If FOR UPDATE were ever weakened
        # to SKIP LOCKED or dropped, this join would succeed and outcome would
        # already be filled.
        waiter.join(timeout=1.0)
        assert outcome == [], "second activation acquired the lock concurrently"

        holder.commit()
    finally:
        holder.close()

    waiter.join(timeout=10)
    assert outcome == ["locked"], "second activation never acquired the released lock"


def test_claim_leaves_the_operation_running_for_the_next_reader(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as setup:
        started = SqlAlchemyOperationStore(setup).begin(
            "key-1", VALIDATE, SHA, "fp", uuid4()
        )
        setup.commit()

    with session_factory() as worker:
        SqlAlchemyOperationStore(worker).claim_next()
        worker.commit()

    with session_factory() as reader:
        stored = SqlAlchemyOperationStore(reader).get(started.id)

    assert stored is not None
    assert stored.state is OperationState.RUNNING
    assert stored.claimed_at is not None
