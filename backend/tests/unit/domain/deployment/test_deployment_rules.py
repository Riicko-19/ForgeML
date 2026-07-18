"""The deployment version state machine, exercised as pure policy."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.deployment.models import (
    DeploymentVersion,
    ResourcePolicy,
    VersionState,
)
from forgeml.domain.deployment.rules import (
    can_transition,
    mark_active,
    mark_built,
    mark_deactivated,
    mark_failed,
    mark_ready,
    mark_stopped,
)
from forgeml.domain.operations.models import OperationFailure

FAILURE = OperationFailure(code="build_failed", message="dependency install failed")


def version(
    state: VersionState = VersionState.BUILDING, **overrides: object
) -> DeploymentVersion:
    now = datetime(2026, 7, 17, tzinfo=UTC)
    base = DeploymentVersion(
        id=uuid4(),
        deployment_id=uuid4(),
        package_id=uuid4(),
        attempt=1,
        state=state,
        resource_policy=ResourcePolicy(),
        created_at=now,
        updated_at=now,
    )
    return base if not overrides else base.__class__(**{**base.__dict__, **overrides})


def test_the_happy_path_walks_building_to_ready() -> None:
    built = mark_built(version(), image_ref="sha256:abc")
    assert built.state is VersionState.STARTING
    assert built.image_ref == "sha256:abc"

    ready = mark_ready(built, container_id="c1", endpoint="http://internal:8000")
    assert ready.state is VersionState.READY
    assert ready.container_id == "c1"
    assert ready.endpoint == "http://internal:8000"


def test_build_and_start_can_fail() -> None:
    assert (
        mark_failed(version(VersionState.BUILDING), FAILURE).state
        is VersionState.FAILED
    )
    assert (
        mark_failed(version(VersionState.STARTING), FAILURE).state
        is VersionState.FAILED
    )


def test_failed_is_terminal_for_the_attempt() -> None:
    assert VersionState.FAILED.is_terminal
    failed = mark_failed(version(VersionState.BUILDING), FAILURE)
    # No transition leaves FAILED; a retry is a new version, not an edge.
    with pytest.raises(AppError):
        mark_built(failed, image_ref="sha256:abc")


def test_ready_can_be_stopped() -> None:
    assert mark_stopped(version(VersionState.READY)).state is VersionState.STOPPED


@pytest.mark.parametrize(
    ("state", "call"),
    [
        (
            VersionState.BUILDING,
            lambda v: mark_ready(v, container_id="c", endpoint="e"),
        ),
        (VersionState.READY, lambda v: mark_built(v, image_ref="i")),
        (VersionState.STARTING, lambda v: mark_stopped(v)),
        (VersionState.STOPPED, lambda v: mark_failed(v, FAILURE)),
    ],
)
def test_illegal_transitions_conflict(state: VersionState, call: object) -> None:
    with pytest.raises(AppError) as captured:
        call(version(state))  # type: ignore[operator]
    assert captured.value.category is ErrorCategory.CONFLICT
    assert captured.value.code == "invalid_state_transition"


def test_ready_active_edge_is_legal_but_module_5_never_drives_it() -> None:
    # Frozen for the routing module (Module 7); the rule permits the edge.
    assert can_transition(VersionState.READY, VersionState.ACTIVE)
    assert can_transition(VersionState.ACTIVE, VersionState.READY)


def test_activation_and_deactivation_walk_the_route_edge() -> None:
    active = mark_active(version(VersionState.READY))
    assert active.state is VersionState.ACTIVE
    assert mark_deactivated(active).state is VersionState.READY


@pytest.mark.parametrize(
    "call",
    [
        lambda v: mark_active(v),
        lambda v: mark_deactivated(version(VersionState.READY)),
    ],
)
def test_activation_from_an_illegal_state_conflicts(call: object) -> None:
    # mark_active on a non-READY version, and mark_deactivated on a READY one.
    with pytest.raises(AppError) as captured:
        call(version(VersionState.BUILDING))  # type: ignore[operator]
    assert captured.value.code == "invalid_state_transition"


def test_transition_returns_a_new_value_and_does_not_mutate() -> None:
    original = version(VersionState.BUILDING)
    mark_built(original, image_ref="sha256:abc")
    assert original.state is VersionState.BUILDING
    assert original.image_ref is None
