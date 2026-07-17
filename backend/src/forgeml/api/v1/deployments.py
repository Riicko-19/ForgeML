"""Deployment routes (docs 12).

The lifecycle-bearing endpoints -- create a version, stop it, reconcile -- are
long-running commands, so they return 202 with a durable operation the client
polls, exactly like package upload. Reads return the resource directly.

Wiring this router into the live application belongs to Module 6: it needs a
real RuntimeManager, and the Docker adapter is that module. Until then the
router is exercised against the fake runtime by the HTTP contract tests.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Query, Response, status

from forgeml.api.schemas import ErrorEnvelope
from forgeml.api.v1.schemas import (
    DEFAULT_PAGE_SIZE,
    CreateDeploymentRequest,
    CreateVersionRequest,
    Cursor,
    DeploymentListResponse,
    DeploymentResource,
    IdempotencyKey,
    OperationResource,
    PageLimit,
    ResourcePolicyModel,
    VersionResource,
    decode_cursor,
    encode_cursor,
)
from forgeml.application.deployment.services import DeploymentService
from forgeml.core.correlation import current_request_id, new_request_id
from forgeml.core.errors import AppError, ErrorCategory

_ERRORS: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorEnvelope},
    404: {"model": ErrorEnvelope},
    409: {"model": ErrorEnvelope},
    422: {"model": ErrorEnvelope},
    500: {"model": ErrorEnvelope},
    503: {"model": ErrorEnvelope},
}


def _correlation_id() -> UUID:
    return UUID(current_request_id() or new_request_id())


def _require_key(idempotency_key: str | None) -> str:
    if idempotency_key is None:
        raise AppError(
            category=ErrorCategory.BAD_REQUEST,
            code="idempotency_key_required",
            message="An Idempotency-Key header is required.",
        )
    return idempotency_key


def create_deployment_router(service: DeploymentService) -> APIRouter:
    """Create the deployment routes bound to the deployment use cases."""

    router = APIRouter(prefix="/deployments", tags=["deployments"])

    @router.post(
        "",
        response_model=DeploymentResource,
        status_code=status.HTTP_201_CREATED,
        responses=_ERRORS,
        summary="Create a named deployment",
    )
    def create_deployment(body: CreateDeploymentRequest) -> DeploymentResource:
        deployment = service.create_deployment(body.name, _correlation_id())
        return DeploymentResource.of(deployment)

    @router.get(
        "",
        response_model=DeploymentListResponse,
        responses=_ERRORS,
        summary="List deployments, newest first",
    )
    def list_deployments(
        limit: Annotated[PageLimit, Query()] = DEFAULT_PAGE_SIZE,
        cursor: Annotated[Cursor | None, Query()] = None,
    ) -> DeploymentListResponse:
        page = service.list_deployments(limit=limit, cursor=decode_cursor(cursor))
        return DeploymentListResponse(
            items=tuple(DeploymentResource.of(item) for item in page.items),
            next_cursor=encode_cursor(page.next_cursor),
        )

    @router.get(
        "/{deployment_id}",
        response_model=DeploymentResource,
        responses=_ERRORS,
        summary="Read one deployment",
    )
    def read_deployment(deployment_id: UUID) -> DeploymentResource:
        return DeploymentResource.of(service.get_deployment(deployment_id))

    @router.post(
        "/{deployment_id}/versions",
        response_model=OperationResource,
        status_code=status.HTTP_202_ACCEPTED,
        responses=_ERRORS,
        summary="Build and start a new version of an accepted package",
    )
    def create_version(
        deployment_id: UUID,
        body: CreateVersionRequest,
        response: Response,
        idempotency_key: Annotated[IdempotencyKey | None, Header()] = None,
    ) -> OperationResource:
        policy = (body.resource_policy or ResourcePolicyModel()).to_domain()
        operation = service.deploy_version(
            deployment_id=deployment_id,
            package_id=body.package_id,
            resource_policy=policy,
            idempotency_key=_require_key(idempotency_key),
            correlation_id=_correlation_id(),
        )
        response.headers["Location"] = f"/v1/operations/{operation.id}"
        return OperationResource.of(operation)

    @router.get(
        "/{deployment_id}/versions/{version_id}",
        response_model=VersionResource,
        responses=_ERRORS,
        summary="Read one deployment version",
    )
    def read_version(deployment_id: UUID, version_id: UUID) -> VersionResource:
        return VersionResource.of(service.get_version(version_id))

    @router.post(
        "/{deployment_id}/versions/{version_id}/stop",
        response_model=OperationResource,
        status_code=status.HTTP_202_ACCEPTED,
        responses=_ERRORS,
        summary="Stop a running version",
    )
    def stop_version(
        deployment_id: UUID,
        version_id: UUID,
        response: Response,
        idempotency_key: Annotated[IdempotencyKey | None, Header()] = None,
    ) -> OperationResource:
        operation = service.stop_version(
            version_id=version_id,
            idempotency_key=_require_key(idempotency_key),
            correlation_id=_correlation_id(),
        )
        response.headers["Location"] = f"/v1/operations/{operation.id}"
        return OperationResource.of(operation)

    return router


def create_admin_router(service: DeploymentService) -> APIRouter:
    """Operator reconciliation route (docs 12)."""

    router = APIRouter(prefix="/admin", tags=["admin"])

    @router.post(
        "/reconcile",
        response_model=OperationResource,
        status_code=status.HTTP_202_ACCEPTED,
        responses=_ERRORS,
        summary="Reconcile runtime resources against records",
    )
    def reconcile(
        response: Response,
        idempotency_key: Annotated[IdempotencyKey | None, Header()] = None,
    ) -> OperationResource:
        operation = service.reconcile(
            idempotency_key=_require_key(idempotency_key),
            correlation_id=_correlation_id(),
        )
        response.headers["Location"] = f"/v1/operations/{operation.id}"
        return OperationResource.of(operation)

    return router
