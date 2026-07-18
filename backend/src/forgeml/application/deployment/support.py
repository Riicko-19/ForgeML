"""Shared plumbing for the deployment use cases (docs 03/04).

Module 5 delivered the deployment lifecycle as one service. It grew five
reasons to change -- reads, build/start, activation, stop, reconciliation --
so ForgeML 0.9 splits it along the seams its own `_execute_*` methods already
described. This module holds what all four of those services genuinely share:
the unit-of-work factory type, the operation bookkeeping every durable command
performs, and the error vocabulary the deployment module speaks.

Nothing here makes a decision. Policy lives in `forgeml.domain.deployment.rules`
and the use cases live beside this file; this is the plumbing they stand on.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from forgeml.application.package.services import is_accepted
from forgeml.application.unit_of_work import UnitOfWork
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.audit.models import ActorType, AuditEvent
from forgeml.domain.deployment.models import DeploymentVersion, VersionState
from forgeml.domain.identity.models import Principal
from forgeml.domain.operations.models import Operation, OperationFailure
from forgeml.domain.package.models import InferenceContract

UnitOfWorkFactory = Callable[[], UnitOfWork]

UNAVAILABLE = OperationFailure(
    code="runtime_unavailable",
    message="the container runtime is unavailable; retry the operation",
)

NOT_HEALTHY = OperationFailure(
    code="candidate_not_healthy",
    message="the candidate version's runtime is not healthy; activation refused",
)


class OperationAwareService:
    """Base for a use case that completes durable operations (ADR-006).

    Every deployment command follows the same shape: claim the operation, do
    the work between committed transactions, then complete or fail it. The
    claiming and the completing are identical everywhere, so they live here and
    the use cases keep only the part that differs.
    """

    def __init__(self, unit_of_work: UnitOfWorkFactory) -> None:
        self._unit_of_work = unit_of_work

    def _save_version(self, version: DeploymentVersion) -> None:
        with self._unit_of_work() as uow:
            uow.deployments.save_version(version)
            uow.commit()

    def _fail_operation(
        self, operation_id: UUID, failure: OperationFailure
    ) -> Operation:
        with self._unit_of_work() as uow:
            failed = uow.operations.fail(operation_id, failure)
            uow.commit()
            return failed

    def _current(self, operation_id: UUID) -> Operation:
        with self._unit_of_work() as uow:
            current = uow.operations.get(operation_id)
        if current is None:  # pragma: no cover - it was just created
            raise missing("operation")
        return current

    @staticmethod
    def _event(
        action: str,
        version: DeploymentVersion,
        correlation_id: UUID,
        principal: Principal | None = None,
    ) -> AuditEvent:
        """One lifecycle audit record, attributed when there is someone to blame.

        `principal` is optional because these events have two origins. A command
        the operator issued carries their identity. The same event re-emitted by
        ADR-016 crash recovery, after the request that asked for it is long
        gone, carries none -- and records SYSTEM, which is what actually
        happened. Inventing an actor for the recovered case would put a false
        claim in an append-only trail.
        """

        return AuditEvent(
            actor_type=ActorType.SYSTEM if principal is None else principal.actor_type,
            actor_id=None if principal is None else principal.actor_id,
            action=f"deployment_version.{action}",
            target_type="deployment_version",
            target_id=str(version.id),
            correlation_id=correlation_id,
            metadata={"attempt": str(version.attempt)},
        )


def missing(what: str) -> AppError:
    """The 404 every deployment read and command raises for an absent record."""

    return AppError(
        category=ErrorCategory.NOT_FOUND,
        code=f"{what}_not_found",
        message=f"the referenced {what.replace('_', ' ')} does not exist",
    )


def not_accepted() -> AppError:
    """Only a validated package may be deployed (docs 12)."""

    return AppError(
        category=ErrorCategory.CONFLICT,
        code="package_not_accepted",
        message="only a validated package can be deployed",
    )


def invalid_transition(state: VersionState, verb: str) -> AppError:
    """A lifecycle command aimed at a version that cannot accept it."""

    return AppError(
        category=ErrorCategory.CONFLICT,
        code="invalid_state_transition",
        message=f"a {state.value} version cannot be {verb}",
    )


def latest_contract(uow: UnitOfWork, package_id: UUID) -> InferenceContract | None:
    """The analyzed contract of an accepted package, or None if not deployable."""

    history = uow.packages.findings_for(package_id)
    latest = history[0] if history else None
    if not is_accepted(latest) or latest is None or latest.contract is None:
        return None
    return latest.contract
