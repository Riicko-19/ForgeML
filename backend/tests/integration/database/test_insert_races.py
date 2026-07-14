"""True insert races, forced rather than hoped for.

The sequential tests never reach the IntegrityError handlers, because the second
caller's SELECT already sees the first caller's committed row. That leaves the
actual race code -- the branch that runs in production when two uploads land at
once -- untested. These tests hold both transactions past their existence check
so that both really do INSERT, and the unique index really does arbitrate.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from forgeml.domain.operations.models import OperationType
from forgeml.infrastructure.database.repositories import (
    SqlAlchemyOperationStore,
    SqlAlchemyPackageCatalog,
)

SHA = "e" * 64
VALIDATE = OperationType.PACKAGE_VALIDATE


def _run_racing(worker: Callable[[], None]) -> list[BaseException]:
    failures: list[BaseException] = []

    def guarded() -> None:
        try:
            worker()
        except BaseException as error:
            # Captured so the assertion reports it; a thread that raised would
            # otherwise die silently and the test would pass on nothing.
            failures.append(error)

    threads = [threading.Thread(target=guarded) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)

    assert not any(thread.is_alive() for thread in threads), "a racing worker hung"
    return failures


def test_two_simultaneous_uploads_resolve_to_one_package(
    session_factory: sessionmaker[Session],
) -> None:
    barrier = threading.Barrier(2)
    identifiers: list[UUID] = []

    def upload() -> None:
        with session_factory() as session:
            catalog = SqlAlchemyPackageCatalog(session)
            lookup = catalog._by_checksum
            seen: list[int] = []

            def gated(sha256: str) -> Any:
                row = lookup(sha256)
                if not seen:
                    # Both transactions have now passed the existence check and
                    # neither has inserted. From here the database, not our code,
                    # decides who wins.
                    seen.append(1)
                    barrier.wait(timeout=10)
                return row

            catalog._by_checksum = gated  # type: ignore[method-assign]
            package = catalog.get_or_create(SHA, "m.forge", 10, f"artifact://{SHA}")
            session.commit()
            identifiers.append(package.id)

    failures = _run_racing(upload)

    assert not failures, f"a racing upload failed: {failures}"
    assert len(identifiers) == 2
    assert identifiers[0] == identifiers[1], "the race created two packages"

    with session_factory() as session:
        stored = SqlAlchemyPackageCatalog(session).find_by_checksum(SHA)
    assert stored is not None
    assert stored.id == identifiers[0]


def test_two_simultaneous_retries_resolve_to_one_operation(
    session_factory: sessionmaker[Session],
) -> None:
    barrier = threading.Barrier(2)
    identifiers: list[UUID] = []

    def submit() -> None:
        with session_factory() as session:
            store = SqlAlchemyOperationStore(session)
            lookup = store._by_key
            seen: list[int] = []

            def gated(key: str, type: OperationType, target: str) -> Any:
                row = lookup(key, type, target)
                if not seen:
                    seen.append(1)
                    barrier.wait(timeout=10)
                return row

            store._by_key = gated  # type: ignore[method-assign,assignment]
            operation = store.begin("key-1", VALIDATE, SHA, "fp", uuid4())
            session.commit()
            identifiers.append(operation.id)

    failures = _run_racing(submit)

    assert not failures, f"a racing retry failed: {failures}"
    assert len(identifiers) == 2
    # If this ever produces two operations, the same work runs twice -- which is
    # exactly what an idempotency key exists to prevent.
    assert identifiers[0] == identifiers[1], "the race created two operations"
