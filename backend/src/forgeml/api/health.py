"""Operational health routes."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from forgeml.api.schemas import ErrorEnvelope, HealthResponse
from forgeml.core.config import AppSettings

ReadinessCheck = Callable[[], None]


def create_health_router(
    settings: AppSettings, check_readiness: ReadinessCheck
) -> APIRouter:
    """Create health routes bound to immutable service identity.

    Liveness answers "is the process up". Readiness answers "can this process
    actually serve", which since Module 2 means the metadata database must
    answer. `check_readiness` raises when it cannot, and the error mapping turns
    that into a 503.
    """

    router = APIRouter()

    error_responses: dict[int | str, dict[str, Any]] = {
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
    def readiness() -> HealthResponse:
        check_readiness()
        return HealthResponse(
            status="ready",
            service="forgeml-control-plane",
            version=settings.service_version,
        )

    return router
