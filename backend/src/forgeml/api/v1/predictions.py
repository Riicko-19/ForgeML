"""Platform prediction route (docs 12).

`POST /v1/deployments/{name}/predict` is the only path a client uses to run a
model: it forwards to the deployment's active version and returns the model's
output. The client never sees a container, an image, or an endpoint (docs 12).
Failures map to the platform envelope -- 422 for bad input, 503 when there is no
active healthy runtime, 502 when the runtime itself fails -- and never leak
runtime detail.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body

from forgeml.api.schemas import ErrorEnvelope
from forgeml.api.v1.schemas import DeploymentName
from forgeml.application.routing.services import RouteManager
from forgeml.core.correlation import current_request_id, new_request_id

_ERRORS: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorEnvelope},
    502: {"model": ErrorEnvelope},
    503: {"model": ErrorEnvelope},
}


def _correlation_id() -> UUID:
    return UUID(current_request_id() or new_request_id())


def create_prediction_router(route_manager: RouteManager) -> APIRouter:
    """Create the prediction route bound to the route manager."""

    router = APIRouter(prefix="/deployments", tags=["predictions"])

    @router.post(
        "/{name}/predict",
        responses=_ERRORS,
        summary="Run a prediction against the deployment's active version",
    )
    def predict(name: DeploymentName, payload: Annotated[Any, Body()]) -> Any:
        return route_manager.predict(name, payload, _correlation_id())

    return router
