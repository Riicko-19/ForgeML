"""The deployment module's use cases, grouped for wiring (docs 03/04).

Module 5 shipped these as one `DeploymentService`. By the end of Module 7 that
class had five reasons to change -- reads, build/start, activation, stop, and
reconciliation -- and ForgeML 0.9 split it along the seams its own `_execute_*`
methods already named. Each service now lives in its own module:

    queries.py         reads, including the routing read model
    lifecycle.py       create, build/start, stop
    activation.py      activation and rollback, the route swap
    reconciliation.py  desired versus observed state

`DeploymentServices` is the bundle, not a facade: it holds the four and forwards
nothing. A caller states which responsibility it is using
(`deployments.activation.activate_version(...)`), which is what makes the next
module's authorization checks land in four small files instead of one large one.

Behaviour is unchanged by the split. The HTTP contract, the state machine, the
transaction boundaries, and the operation semantics are exactly as Module 7 left
them.
"""

from __future__ import annotations

from dataclasses import dataclass

from forgeml.application.deployment.activation import ActivationService
from forgeml.application.deployment.lifecycle import DeploymentLifecycleService
from forgeml.application.deployment.queries import DeploymentQueryService
from forgeml.application.deployment.reconciliation import ReconciliationService
from forgeml.application.deployment.support import UnitOfWorkFactory
from forgeml.domain.deployment.ports import RuntimeManager

__all__ = [
    "ActivationService",
    "DeploymentLifecycleService",
    "DeploymentQueryService",
    "DeploymentServices",
    "ReconciliationService",
    "UnitOfWorkFactory",
]


@dataclass(frozen=True, slots=True)
class DeploymentServices:
    """The deployment use cases, wired once and shared by the routes."""

    queries: DeploymentQueryService
    lifecycle: DeploymentLifecycleService
    activation: ActivationService
    reconciliation: ReconciliationService

    @classmethod
    def create(
        cls, unit_of_work: UnitOfWorkFactory, runtime: RuntimeManager
    ) -> DeploymentServices:
        """Build the four services over one unit of work and one runtime."""

        return cls(
            queries=DeploymentQueryService(unit_of_work),
            lifecycle=DeploymentLifecycleService(unit_of_work, runtime),
            activation=ActivationService(unit_of_work, runtime),
            reconciliation=ReconciliationService(unit_of_work, runtime),
        )
