"""FastAPI application composition root."""

from fastapi import FastAPI

from forgeml.api.error_handlers import register_error_handlers
from forgeml.api.health import create_health_router
from forgeml.api.middleware import RequestContextMiddleware
from forgeml.core.config import AppSettings


def create_application(settings: AppSettings) -> FastAPI:
    """Create an isolated Module 0 application without provider side effects."""

    app = FastAPI(
        title="ForgeML Control Plane",
        version=settings.service_version,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    register_error_handlers(app)
    app.include_router(create_health_router(settings))
    app.add_middleware(RequestContextMiddleware)
    return app
