"""Operation polling route (ADR-006)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter

from forgeml.api.schemas import ErrorEnvelope
from forgeml.api.v1.schemas import OperationResource
from forgeml.application.operations.services import OperationService

# 422 must be declared explicitly. FastAPI otherwise documents its own
# HTTPValidationError shape for any route with a validated parameter, while the
# handler actually returns the frozen ForgeML envelope -- so a client generated
# from the published schema would parse the wrong body.
_ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorEnvelope},
    422: {"model": ErrorEnvelope},
    500: {"model": ErrorEnvelope},
    503: {"model": ErrorEnvelope},
}


def create_operation_router(service: OperationService) -> APIRouter:
    """Create the operation routes bound to the operation use cases."""

    router = APIRouter(prefix="/operations", tags=["operations"])

    @router.get(
        "/{operation_id}",
        response_model=OperationResource,
        responses=_ERRORS,
        summary="Poll a durable operation",
    )
    def read_operation(operation_id: UUID) -> OperationResource:
        return OperationResource.of(service.get(operation_id))

    return router
