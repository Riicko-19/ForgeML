"""Operational health routes."""

from fastapi import APIRouter

from forgeml.api.schemas import ErrorEnvelope, HealthResponse
from forgeml.core.config import AppSettings


def create_health_router(settings: AppSettings) -> APIRouter:
    """Create health routes bound to immutable service identity."""

    router = APIRouter()

    error_responses = {
        405: {"model": ErrorEnvelope},
        500: {"model": ErrorEnvelope},
        503: {"model": ErrorEnvelope},
    }

    @router.get(
        "/healthz",
        response_model=HealthResponse,
        responses=error_responses,
    )
    async def liveness() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service="forgeml-control-plane",
            version=settings.service_version,
        )

    @router.get(
        "/readyz",
        response_model=HealthResponse,
        responses=error_responses,
    )
    async def readiness() -> HealthResponse:
        return HealthResponse(
            status="ready",
            service="forgeml-control-plane",
            version=settings.service_version,
        )

    return router
