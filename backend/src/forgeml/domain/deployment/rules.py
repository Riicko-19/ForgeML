"""Deployment version lifecycle policy (docs 03/04).

Pure functions over `DeploymentVersion` values, following package/rules.py: the
state machine and its preconditions live here, not in the service or the ORM. An
invalid transition raises a CONFLICT the API maps to 409 invalid_state_transition
(docs 04); a Docker observation can never *drive* one of these, it only reports.

Module 5 drives BUILDING -> STARTING -> READY and the FAILED/STOPPED branches;
the routing module (Module 7) drives READY <-> ACTIVE through `mark_active` and
`mark_deactivated`, only after a candidate's runtime is confirmed healthy.
"""

from __future__ import annotations

from dataclasses import replace

from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.deployment.models import DeploymentVersion, VersionState
from forgeml.domain.operations.models import OperationFailure

_TRANSITIONS: dict[VersionState, frozenset[VersionState]] = {
    VersionState.BUILDING: frozenset({VersionState.STARTING, VersionState.FAILED}),
    VersionState.STARTING: frozenset({VersionState.READY, VersionState.FAILED}),
    VersionState.READY: frozenset({VersionState.ACTIVE, VersionState.STOPPED}),
    VersionState.ACTIVE: frozenset({VersionState.READY, VersionState.STOPPED}),
    VersionState.STOPPED: frozenset({VersionState.STARTING}),
    VersionState.FAILED: frozenset(),
}


def can_transition(current: VersionState, target: VersionState) -> bool:
    """Report whether a version may move from one state to another."""

    return target in _TRANSITIONS[current]


def _guard(current: VersionState, target: VersionState) -> None:
    if not can_transition(current, target):
        raise AppError(
            category=ErrorCategory.CONFLICT,
            code="invalid_state_transition",
            message=f"a {current.value} version cannot become {target.value}",
        )


def mark_built(version: DeploymentVersion, *, image_ref: str) -> DeploymentVersion:
    """BUILDING -> STARTING once the image reference is known (docs 04)."""

    _guard(version.state, VersionState.STARTING)
    return replace(version, state=VersionState.STARTING, image_ref=image_ref)


def mark_ready(
    version: DeploymentVersion, *, container_id: str, endpoint: str
) -> DeploymentVersion:
    """STARTING -> READY once the container is running and healthy (docs 04)."""

    _guard(version.state, VersionState.READY)
    return replace(
        version,
        state=VersionState.READY,
        container_id=container_id,
        endpoint=endpoint,
    )


def mark_active(version: DeploymentVersion) -> DeploymentVersion:
    """READY -> ACTIVE once the platform route points at this version (docs 04).

    The routing module (Module 7) drives this only after the candidate's runtime
    is confirmed healthy; a Docker observation never promotes a version itself.
    """

    _guard(version.state, VersionState.ACTIVE)
    return replace(version, state=VersionState.ACTIVE)


def mark_deactivated(version: DeploymentVersion) -> DeploymentVersion:
    """ACTIVE -> READY when a replacement version takes the route (docs 04).

    The previous active version stays runnable (READY), not stopped: a rollback
    is simply activating it again.
    """

    _guard(version.state, VersionState.READY)
    return replace(version, state=VersionState.READY)


def mark_failed(
    version: DeploymentVersion, failure: OperationFailure
) -> DeploymentVersion:
    """Fail the current attempt with a safe, classified diagnosis (docs 04).

    Legal from BUILDING or STARTING; FAILED is terminal for the attempt, and a
    retry is a new version rather than a transition back out of FAILED.
    """

    _guard(version.state, VersionState.FAILED)
    return replace(version, state=VersionState.FAILED, failure=failure)


def mark_stopped(version: DeploymentVersion) -> DeploymentVersion:
    """READY/ACTIVE -> STOPPED. The caller removes any route first (docs 04)."""

    _guard(version.state, VersionState.STOPPED)
    return replace(version, state=VersionState.STOPPED)
