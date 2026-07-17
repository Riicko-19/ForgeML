"""Immutable deployment records and lifecycle states (docs 03/04).

A deployment is a stable name an operator points at a succession of versions. A
deployment *version* is one immutable build/run attempt of an accepted package:
its state walks the runtime lifecycle (BUILDING -> STARTING -> READY, or FAILED),
and a retry is always a new attempt, never a mutation of an old one (docs 04).

The records here are pure values -- the transition policy over them lives in
rules.py, the same split package/models.py and package/rules.py already use.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from forgeml.domain.operations.models import OperationFailure


class DesiredState(StrEnum):
    """What the operator wants a deployment to be doing.

    Desired state is the operator's intent; a version's `VersionState` is the
    observed lifecycle of one attempt. Reconciliation compares the two.
    """

    RUNNING = "running"
    STOPPED = "stopped"


class VersionState(StrEnum):
    """The lifecycle of one immutable deployment version/attempt (docs 03/04).

    BUILDING/STARTING/READY/FAILED/STOPPED are driven by Module 5 against the
    runtime. ACTIVE and the route it implies are frozen here but owned by the
    routing module (Module 7); nothing in this module transitions a version
    into or out of ACTIVE.
    """

    BUILDING = "building"
    STARTING = "starting"
    READY = "ready"
    ACTIVE = "active"
    FAILED = "failed"
    STOPPED = "stopped"

    @property
    def is_terminal(self) -> bool:
        # FAILED is terminal for an attempt; retry creates a new version.
        return self is VersionState.FAILED


@dataclass(frozen=True, slots=True)
class ResourcePolicy:
    """Resolved runtime resource bounds for a version (docs 12).

    Requested in the manifest, bounded by server policy at deploy time. None
    means "use the server default", resolved by the deployment service; the
    record stores whatever was resolved for this immutable attempt.
    """

    cpu_millicores: int | None = None
    memory_mib: int | None = None
    pids_limit: int | None = None


@dataclass(frozen=True, slots=True)
class Deployment:
    """A named deployment. The name is immutable and DNS-label shaped (docs 12)."""

    id: UUID
    name: str
    desired_state: DesiredState
    created_at: datetime
    updated_at: datetime
    active_version_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class DeploymentVersion:
    """One immutable build/run attempt of an accepted package (docs 04).

    `attempt` is monotonic per deployment. `image_ref` and `container_id` are the
    provider-neutral identities persisted as the runtime produces them; they are
    None until the lifecycle reaches the stage that yields them. `failure` is set
    only on a FAILED attempt and carries a safe, classified diagnosis.
    """

    id: UUID
    deployment_id: UUID
    package_id: UUID
    attempt: int
    state: VersionState
    resource_policy: ResourcePolicy
    created_at: datetime
    updated_at: datetime
    image_ref: str | None = None
    container_id: str | None = None
    endpoint: str | None = None
    failure: OperationFailure | None = None
