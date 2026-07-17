"""The fake RuntimeManager honours the provider-neutral port contract."""

from __future__ import annotations

from uuid import uuid4

import pytest

from forgeml.domain.deployment.models import ResourcePolicy
from forgeml.domain.deployment.ports import (
    RuntimeExecutionError,
    RuntimeUnavailable,
)
from forgeml.domain.operations.models import OperationFailure
from forgeml.domain.package.analyzer import analyze
from forgeml.domain.package.generator import generate
from forgeml.domain.package.models import ManifestV1
from tests.fake_runtime import FakeRuntimeManager
from tests.packages import VALID_MANIFEST

CONTEXT = generate(
    analyze(ManifestV1.model_validate(VALID_MANIFEST)), checksum="a" * 64
)
POLICY = ResourcePolicy()


def test_build_start_inspect_and_reconcile_happy_path() -> None:
    runtime = FakeRuntimeManager()
    version_id = uuid4()

    image = runtime.build(version_id, CONTEXT, POLICY)
    assert image.image_ref.startswith("forgeml/")

    container = runtime.start(version_id, image, POLICY)
    assert container.container_id
    assert container.endpoint.endswith(":8000")

    status = runtime.inspect(container.container_id)
    assert status.present and status.running and status.healthy

    managed = runtime.reconcile()
    assert [m.version_id for m in managed] == [version_id]


def test_stop_removes_the_container() -> None:
    runtime = FakeRuntimeManager()
    container = runtime.start(uuid4(), runtime.build(uuid4(), CONTEXT, POLICY), POLICY)
    runtime.stop(container.container_id)
    assert runtime.inspect(container.container_id).present is False
    assert runtime.reconcile() == ()
    # Stopping an absent container is not an error.
    runtime.stop("absent")


def test_build_failure_is_a_terminal_execution_error() -> None:
    runtime = FakeRuntimeManager()
    runtime.build_failure = OperationFailure(code="build_failed", message="install")
    with pytest.raises(RuntimeExecutionError) as captured:
        runtime.build(uuid4(), CONTEXT, POLICY)
    assert captured.value.failure.code == "build_failed"


def test_start_failure_is_a_terminal_execution_error() -> None:
    runtime = FakeRuntimeManager()
    runtime.start_failure = OperationFailure(code="readiness_timeout", message="slow")
    image = runtime.build(uuid4(), CONTEXT, POLICY)
    with pytest.raises(RuntimeExecutionError):
        runtime.start(uuid4(), image, POLICY)


def test_docker_unavailable_is_retriable() -> None:
    runtime = FakeRuntimeManager()
    runtime.available = False
    with pytest.raises(RuntimeUnavailable):
        runtime.build(uuid4(), CONTEXT, POLICY)


def test_an_unhealthy_container_is_reported_not_raised() -> None:
    runtime = FakeRuntimeManager()
    runtime.healthy = False
    container = runtime.start(uuid4(), runtime.build(uuid4(), CONTEXT, POLICY), POLICY)
    assert runtime.inspect(container.container_id).healthy is False
