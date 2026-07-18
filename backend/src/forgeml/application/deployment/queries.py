"""Deployment reads (docs 03/04).

Queries only: nothing here changes state, takes a lock, or touches the runtime.
Keeping them apart from the lifecycle commands means the read path can be
authorized, cached, or served from a replica later without disturbing the
commands -- and it makes the command services small enough to read in one sitting.

`resolve_active_target` is the routing module's read model. It lives here rather
than in `RouteManager` so that routing never reaches a repository directly
(docs 04); it returns a routing-owned value object, which is the one place the
deployment module knows routing exists.
"""

from __future__ import annotations

from uuid import UUID

from forgeml.application.deployment.support import (
    OperationAwareService,
    latest_contract,
    missing,
)
from forgeml.domain.deployment.models import Deployment, DeploymentVersion, VersionState
from forgeml.domain.deployment.ports import DeploymentPage
from forgeml.domain.routing.ports import ActiveTarget


class DeploymentQueryService(OperationAwareService):
    """Reads deployments, versions, and the active routing target."""

    def get_deployment(self, deployment_id: UUID) -> Deployment:
        with self._unit_of_work() as uow:
            deployment = uow.deployments.find_deployment(deployment_id)
        if deployment is None:
            raise missing("deployment")
        return deployment

    def list_deployments(self, limit: int, cursor: str | None) -> DeploymentPage:
        with self._unit_of_work() as uow:
            return uow.deployments.list_deployments(limit=limit, cursor=cursor)

    def get_version(self, version_id: UUID) -> DeploymentVersion:
        with self._unit_of_work() as uow:
            version = uow.deployments.find_version(version_id)
        if version is None:
            raise missing("deployment_version")
        return version

    def resolve_active_target(self, name: str) -> ActiveTarget | None:
        """The routing target for a deployment's active version, or None.

        None means "no active healthy target to route to" for every reason the
        route manager treats alike (docs 12: 503 deployment_unavailable): the
        deployment or its active version is absent, the version is not ACTIVE, it
        has no endpoint, or its contract is gone.
        """

        with self._unit_of_work() as uow:
            deployment = uow.deployments.find_deployment_by_name(name)
            if deployment is None or deployment.active_version_id is None:
                return None
            version = uow.deployments.find_version(deployment.active_version_id)
            if (
                version is None
                or version.state is not VersionState.ACTIVE
                or version.endpoint is None
                or version.container_id is None
            ):
                return None
            contract = latest_contract(uow, version.package_id)
            if contract is None:
                return None
            return ActiveTarget(
                endpoint=version.endpoint,
                container_id=version.container_id,
                input_schema=contract.input_schema,
                output_schema=contract.output_schema,
            )
