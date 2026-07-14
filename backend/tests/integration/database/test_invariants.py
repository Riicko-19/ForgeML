"""Invariants the database enforces, independently of our repositories.

These tests bypass the repository layer on purpose. ADR-004 anticipates an
operator with a psql prompt, so the question is not "does our code preserve the
invariant" but "can the invariant be broken at all".
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError


def _insert_package(engine: Engine, sha256: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO packages "
                "(id, sha256, filename, size_bytes, manifest_version, state,"
                " artifact_uri, created_at, updated_at) "
                "VALUES (:id, :sha, 'm.forge', 10, 1, 'draft', :uri, now(), now())"
            ),
            {"id": uuid4(), "sha": sha256, "uri": f"artifact://{sha256}"},
        )


def test_a_package_checksum_cannot_be_rewritten(engine: Engine) -> None:
    sha = "1" * 64
    _insert_package(engine, sha)

    with pytest.raises(DBAPIError, match="immutable"), engine.begin() as connection:
        connection.execute(
            text("UPDATE packages SET sha256 = :new WHERE sha256 = :old"),
            {"new": "2" * 64, "old": sha},
        )


def test_a_package_artifact_cannot_be_repointed(engine: Engine) -> None:
    sha = "3" * 64
    _insert_package(engine, sha)

    with pytest.raises(DBAPIError, match="immutable"), engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE packages SET artifact_uri = 'artifact://evil' WHERE sha256 = :s"
            ),
            {"s": sha},
        )


def test_a_package_state_may_still_advance(engine: Engine) -> None:
    sha = "4" * 64
    _insert_package(engine, sha)

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE packages SET state = 'validated' WHERE sha256 = :s"),
            {"s": sha},
        )
        state = connection.execute(
            text("SELECT state FROM packages WHERE sha256 = :s"), {"s": sha}
        ).scalar_one()

    assert state == "validated"


def test_two_packages_cannot_share_a_checksum(engine: Engine) -> None:
    sha = "5" * 64
    _insert_package(engine, sha)

    with pytest.raises(IntegrityError):
        _insert_package(engine, sha)


def test_a_terminal_operation_cannot_be_rewritten(engine: Engine) -> None:
    operation_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO operations (id, idempotency_key, type, target_id,"
                " request_fingerprint, state, correlation_id, attempts,"
                " created_at, updated_at) "
                "VALUES (:id, 'k', 'package_validate', 't', 'fp', 'succeeded',"
                " :cid, 1, now(), now())"
            ),
            {"id": operation_id, "cid": uuid4()},
        )

    with pytest.raises(DBAPIError, match="terminal"), engine.begin() as connection:
        connection.execute(
            text("UPDATE operations SET state = 'pending' WHERE id = :id"),
            {"id": operation_id},
        )


def test_an_audit_event_cannot_be_altered_or_deleted(engine: Engine) -> None:
    event_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO audit_events (id, actor_type, action, target_type,"
                " target_id, correlation_id, metadata, occurred_at) "
                "VALUES (:id, 'operator', 'package.validated', 'package', 't',"
                " :cid, '{}'::jsonb, now())"
            ),
            {"id": event_id, "cid": uuid4()},
        )

    with pytest.raises(DBAPIError, match="append-only"), engine.begin() as connection:
        connection.execute(
            text("UPDATE audit_events SET action = 'forged' WHERE id = :id"),
            {"id": event_id},
        )

    with pytest.raises(DBAPIError, match="append-only"), engine.begin() as connection:
        connection.execute(
            text("DELETE FROM audit_events WHERE id = :id"), {"id": event_id}
        )


def test_an_unknown_package_state_is_refused(engine: Engine) -> None:
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO packages (id, sha256, filename, size_bytes,"
                " manifest_version, state, artifact_uri, created_at, updated_at) "
                "VALUES (:id, :sha, 'm.forge', 10, 1, 'invented', 'artifact://x',"
                " now(), now())"
            ),
            {"id": uuid4(), "sha": "6" * 64},
        )


def test_a_package_cannot_have_zero_size(engine: Engine) -> None:
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO packages (id, sha256, filename, size_bytes,"
                " manifest_version, state, artifact_uri, created_at, updated_at) "
                "VALUES (:id, :sha, 'm.forge', 0, 1, 'draft', 'artifact://x',"
                " now(), now())"
            ),
            {"id": uuid4(), "sha": "7" * 64},
        )
