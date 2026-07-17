"""Ports the deployment module drives (docs 04).

`RuntimeManager` is the provider-neutral boundary in front of Docker: the module
speaks in image references, container ids, and health, never in SDK objects, so
the real adapter (Module 6) can be swapped in without touching lifecycle policy.
It is deliberately *not* part of the unit of work -- docs 04 forbids a database
transaction spanning a build, start, or stop, so runtime work always happens
outside the metadata transaction.

`DeploymentRepository` is metadata persistence and therefore belongs on the unit
of work with the other repositories.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from forgeml.domain.deployment.models import (
    Deployment,
    DeploymentVersion,
    DesiredState,
    ResourcePolicy,
)
from forgeml.domain.operations.models import OperationFailure
from forgeml.domain.package.generator import GeneratedBuildContext


@dataclass(frozen=True, slots=True)
class BuiltImage:
    """A built runtime image, addressed provider-neutrally."""

    image_ref: str


@dataclass(frozen=True, slots=True)
class RunningContainer:
    """A started container and the internal endpoint it serves on."""

    container_id: str
    endpoint: str


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """What an inspection can observe about one container (docs 11).

    An observation, never a command: docs 04 says a Docker observation cannot by
    itself promote a version to READY or ACTIVE.
    """

    present: bool
    running: bool
    healthy: bool
    restart_count: int


@dataclass(frozen=True, slots=True)
class ManagedRuntime:
    """A ForgeML-labelled runtime resource seen during reconciliation (ADR-004)."""

    container_id: str
    version_id: UUID | None
    status: RuntimeStatus


class RuntimeUnavailable(Exception):
    """Docker itself is unreachable. Retriable; the API maps this to 503."""


class RuntimeExecutionError(Exception):
    """A build or start genuinely failed. Terminal for the attempt.

    Carries a safe, classified failure the service records on the version and the
    operation (docs 04: FAILED with retained diagnosis, never a trace).
    """

    def __init__(self, failure: OperationFailure) -> None:
        super().__init__(failure.message)
        self.failure = failure


class RuntimeManager(Protocol):
    """Provider-neutral runtime primitives (docs 04). Labels/idempotency.

    Raises RuntimeUnavailable when Docker is unreachable and RuntimeExecutionError
    when the operation itself fails. Module 6 implements this against Docker;
    logs and usage sampling arrive with monitoring (Module 8).
    """

    def build(
        self, version_id: UUID, context: GeneratedBuildContext, policy: ResourcePolicy
    ) -> BuiltImage:
        """Build the image for a version from its generated build context."""

    def start(
        self, version_id: UUID, image: BuiltImage, policy: ResourcePolicy
    ) -> RunningContainer:
        """Start a container for a built image and wait for readiness."""

    def stop(self, container_id: str) -> None:
        """Stop and remove a container. Stopping an absent one is not an error."""

    def inspect(self, container_id: str) -> RuntimeStatus:
        """Observe one container's current state and health."""

    def reconcile(self) -> tuple[ManagedRuntime, ...]:
        """Enumerate ForgeML-labelled runtime resources and their status."""


@dataclass(frozen=True, slots=True)
class DeploymentPage:
    """One page of deployments, newest first."""

    items: tuple[Deployment, ...]
    next_cursor: str | None


class DeploymentRepository(Protocol):
    """Durable deployment and version records with a transactional lock."""

    def create_deployment(self, name: str, desired_state: DesiredState) -> Deployment:
        """Create a named deployment. A duplicate name raises CONFLICT (docs 12)."""

    def find_deployment(self, deployment_id: UUID) -> Deployment | None:
        """Read one deployment by id."""

    def find_deployment_by_name(self, name: str) -> Deployment | None:
        """Read one deployment by its immutable name."""

    def list_deployments(self, limit: int, cursor: str | None = None) -> DeploymentPage:
        """List deployments newest first, bounded by limit."""

    def lock_deployment(self, deployment_id: UUID) -> Deployment | None:
        """Lock a deployment for update (the activation lock, docs 04).

        Frozen here for the routing module (Module 7); Module 5 does not activate.
        """

    def save_deployment(self, deployment: Deployment) -> None:
        """Persist changes to a deployment (desired state, active version)."""

    def add_version(self, version: DeploymentVersion) -> None:
        """Persist a new immutable version attempt."""

    def find_version(self, version_id: UUID) -> DeploymentVersion | None:
        """Read one version by id."""

    def list_versions(self, deployment_id: UUID) -> tuple[DeploymentVersion, ...]:
        """Read a deployment's versions, newest attempt first."""

    def save_version(self, version: DeploymentVersion) -> None:
        """Persist a version's lifecycle transition."""

    def next_attempt(self, deployment_id: UUID, package_id: UUID) -> int:
        """The next monotonic attempt number for this deployment and package."""
