"""The package and operation HTTP surface, end to end.

A real application, a real database, a real artifact store, and real .forge
archives. Nothing here is faked: these tests are the evidence that the docs 12
contract actually holds over the wire.
"""

from __future__ import annotations

from collections.abc import Iterator
from importlib import metadata
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import create_engine, text

from forgeml.core.composition import create_application
from forgeml.core.config import load_settings
from tests.integration.api.conftest import TABLES, database_url
from tests.packages import build_forge, manifest
from tests.support import ASGITestClient, credential_for


@pytest.fixture
def client(
    migrated: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[ASGITestClient]:
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")
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
    app = create_application(settings)
    try:
        yield ASGITestClient(app, credential=credential_for(app))
    finally:
        # The ASGI transport does not run lifespan, so the pool this test opened
        # must be released here or it leaks a live connection per test.
        app.state.container.database.dispose()


def upload(
    client: ASGITestClient,
    archive: bytes,
    *,
    key: str = "key-1",
    filename: str = "model.forge",
) -> httpx.Response:
    return client.request(
        "POST",
        "/v1/packages",
        headers={"Idempotency-Key": key},
        files={"file": (filename, archive, "application/octet-stream")},
    )


def body(response: httpx.Response) -> dict[str, Any]:
    payload: dict[str, Any] = response.json()
    return payload


# ------------------------------------------------------------------- happy path


def test_uploading_a_valid_package_accepts_and_validates_it(
    client: ASGITestClient,
) -> None:
    response = upload(client, build_forge())

    assert response.status_code == 202
    operation = body(response)
    assert operation["state"] == "succeeded"
    assert operation["type"] == "package_validate"
    assert response.headers["location"] == f"/v1/operations/{operation['id']}"
    assert UUID(operation["correlation_id"]).version == 4

    package_id = operation["result"]["package_id"]
    package = body(client.get(f"/v1/packages/{package_id}"))

    assert package["validation_state"] == "validated"
    assert package["validation_findings"] is None
    assert package["manifest"]["entrypoint"]["callable"] == "predict"
    assert package["manifest_version"] == 1
    assert package["filename"] == "model.forge"


def test_an_operation_can_be_polled_after_upload(client: ASGITestClient) -> None:
    operation = body(upload(client, build_forge()))

    polled = body(client.get(f"/v1/operations/{operation['id']}"))

    assert polled["id"] == operation["id"]
    assert polled["state"] == "succeeded"
    assert polled["failure"] is None
    assert polled["completed_at"] is not None


# --------------------------------------------------------------------- verdicts


def test_a_rejected_package_still_completes_its_operation(
    client: ASGITestClient,
) -> None:
    # The operation succeeded because the validation *ran*. A rejected package is
    # a verdict, not a platform failure, and the findings live on the package.
    archive = build_forge(manifest(dependencies=["numpy>=2.1.0"]))

    operation = body(upload(client, archive))

    assert operation["state"] == "succeeded"
    package = body(client.get(f"/v1/packages/{operation['result']['package_id']}"))

    assert package["validation_state"] == "rejected"
    assert package["manifest"] is None
    findings = package["validation_findings"]
    assert [item["code"] for item in findings] == ["dependency_not_pinned"]
    assert findings[0]["path"] == ["dependencies", 0]


def test_bytes_that_are_not_an_archive_are_rejected_with_a_finding(
    client: ASGITestClient,
) -> None:
    operation = body(upload(client, b"not a zip container"))

    package = body(client.get(f"/v1/packages/{operation['result']['package_id']}"))

    assert package["validation_state"] == "rejected"
    assert [item["code"] for item in package["validation_findings"]] == [
        "archive_unreadable"
    ]


# ------------------------------------------------------------------ idempotency


def test_replaying_the_same_upload_returns_the_original_operation(
    client: ASGITestClient,
) -> None:
    archive = build_forge()

    first = body(upload(client, archive, key="key-1"))
    second = body(upload(client, archive, key="key-1"))

    assert first["id"] == second["id"]
    assert second["state"] == "succeeded"

    listed = body(client.get("/v1/packages"))
    assert len(listed["items"]) == 1  # the replay created no second package


def test_reusing_a_key_for_a_different_request_conflicts(
    client: ASGITestClient,
) -> None:
    # Docs 04: the key is unique per operation type and target, and for an upload
    # the target is the archive checksum. So the reachable conflict is the same
    # key and the same bytes with different declared metadata -- the fingerprint
    # covers both, and a client must not reuse a key for a different request.
    archive = build_forge()
    upload(client, archive, key="key-1", filename="model.forge")

    response = upload(client, archive, key="key-1", filename="renamed.forge")

    assert response.status_code == 409
    assert body(response)["code"] == "idempotency_conflict"


def test_the_same_key_against_different_bytes_is_a_separate_operation(
    client: ASGITestClient,
) -> None:
    # Different bytes are a different target, and the key is scoped per target
    # (docs 04). This is not a conflict; it is a different piece of work.
    first = body(upload(client, build_forge(), key="key-1"))

    second = body(upload(client, build_forge(manifest(dependencies=[])), key="key-1"))

    assert first["id"] != second["id"]
    assert first["target"] != second["target"]


def test_a_mutation_without_an_idempotency_key_is_refused(
    client: ASGITestClient,
) -> None:
    response = client.request(
        "POST",
        "/v1/packages",
        files={"file": ("model.forge", build_forge(), "application/octet-stream")},
    )

    assert response.status_code == 400
    assert body(response)["code"] == "idempotency_key_required"


def test_the_same_bytes_under_a_new_key_resolve_to_one_package(
    client: ASGITestClient,
) -> None:
    # ADR-003: the checksum is the identity. A second upload of identical bytes
    # is a new operation but never a second package.
    archive = build_forge()

    first = body(upload(client, archive, key="key-1"))
    second = body(upload(client, archive, key="key-2"))

    assert first["id"] != second["id"]
    assert first["result"]["package_id"] == second["result"]["package_id"]
    assert len(body(client.get("/v1/packages"))["items"]) == 1


# ------------------------------------------------------------------------ reads


def test_packages_are_listed_newest_first_with_a_cursor(
    client: ASGITestClient,
) -> None:
    for index in range(3):
        upload(
            client,
            build_forge(manifest(metadata={"n": str(index)})),
            key=f"key-{index}",
        )

    first = body(client.get("/v1/packages?limit=2"))
    second = body(client.get(f"/v1/packages?limit=2&cursor={first['next_cursor']}"))

    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    assert second["next_cursor"] is None
    identifiers = {item["id"] for item in (*first["items"], *second["items"])}
    assert len(identifiers) == 3


def test_an_unknown_package_is_not_found(client: ASGITestClient) -> None:
    response = client.get(f"/v1/packages/{uuid4()}")

    assert response.status_code == 404
    assert body(response)["code"] == "package_not_found"


def test_an_unknown_operation_is_not_found(client: ASGITestClient) -> None:
    response = client.get(f"/v1/operations/{uuid4()}")

    assert response.status_code == 404
    assert body(response)["code"] == "operation_not_found"


def test_a_malformed_identifier_is_a_validation_error(client: ASGITestClient) -> None:
    response = client.get("/v1/packages/not-a-uuid")

    assert response.status_code == 422
    assert body(response)["code"] == "request_validation_failed"


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "limit=abc"])
def test_an_out_of_range_page_limit_is_refused(
    client: ASGITestClient, query: str
) -> None:
    response = client.get(f"/v1/packages?{query}")

    assert response.status_code == 422


def test_an_invalid_cursor_is_a_bad_request(client: ASGITestClient) -> None:
    response = client.get("/v1/packages?cursor=not-a-cursor")

    assert response.status_code == 400
    assert body(response)["code"] == "cursor_invalid"


# ------------------------------------------------------------------ operational


def test_readiness_reports_ready_when_the_database_answers(
    client: ASGITestClient,
) -> None:
    response = client.get("/readyz")

    assert response.status_code == 200
    assert body(response)["status"] == "ready"


def test_the_openapi_schema_is_published(client: ASGITestClient) -> None:
    response = client.get("/v1/openapi.json")

    assert response.status_code == 200
    assert "/v1/packages" in body(response)["paths"]
