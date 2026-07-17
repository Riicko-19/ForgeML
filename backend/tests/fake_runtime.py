"""A scriptable in-memory RuntimeManager for deployment lifecycle tests.

Module 5 is specified against a fake runtime (docs 06 exit gate): the real
Docker adapter is Module 6. This fake honours the RuntimeManager contract and
lets a test choose the outcome of each primitive -- succeed, fail terminally, or
report Docker unavailable -- so every transition, failure, and recovery branch
can be driven deterministically without Docker.
"""

from __future__ import annotations

from uuid import UUID

from forgeml.domain.deployment.models import ResourcePolicy
from forgeml.domain.deployment.ports import (
    BuiltImage,
    ManagedRuntime,
    RunningContainer,
    RuntimeExecutionError,
    RuntimeStatus,
    RuntimeUnavailable,
)
from forgeml.domain.operations.models import OperationFailure
from forgeml.domain.package.generator import GeneratedBuildContext


class FakeRuntimeManager:
    def __init__(self) -> None:
        self.available = True
        self.build_failure: OperationFailure | None = None
        self.start_failure: OperationFailure | None = None
        self.healthy = True
        self._containers: dict[str, ManagedRuntime] = {}
        self._counter = 0

    def build(
        self,
        version_id: UUID,
        context: GeneratedBuildContext,
        artifact_sha256: str,
        policy: ResourcePolicy,
    ) -> BuiltImage:
        self._require_available()
        if self.build_failure is not None:
            raise RuntimeExecutionError(self.build_failure)
        # Deterministic image reference from the context's artifact identity.
        return BuiltImage(image_ref=f"forgeml/{context.identity[:12]}")

    def start(
        self, version_id: UUID, image: BuiltImage, policy: ResourcePolicy
    ) -> RunningContainer:
        self._require_available()
        if self.start_failure is not None:
            raise RuntimeExecutionError(self.start_failure)
        self._counter += 1
        container_id = f"c{self._counter}"
        self._containers[container_id] = ManagedRuntime(
            container_id=container_id,
            version_id=version_id,
            status=RuntimeStatus(
                present=True, running=True, healthy=self.healthy, restart_count=0
            ),
        )
        return RunningContainer(
            container_id=container_id, endpoint=f"http://{container_id}.internal:8000"
        )

    def stop(self, container_id: str) -> None:
        self._require_available()
        self._containers.pop(container_id, None)

    def inspect(self, container_id: str) -> RuntimeStatus:
        self._require_available()
        managed = self._containers.get(container_id)
        if managed is None:
            return RuntimeStatus(
                present=False, running=False, healthy=False, restart_count=0
            )
        return managed.status

    def reconcile(self) -> tuple[ManagedRuntime, ...]:
        self._require_available()
        return tuple(self._containers.values())

    def _require_available(self) -> None:
        if not self.available:
            raise RuntimeUnavailable("docker is unavailable")
