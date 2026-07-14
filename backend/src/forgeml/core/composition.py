"""FastAPI application composition root."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from forgeml.api.error_handlers import register_error_handlers
from forgeml.api.health import create_health_router
from forgeml.api.middleware import RequestContextMiddleware
from forgeml.api.v1.operations import create_operation_router
from forgeml.api.v1.packages import create_package_router
from forgeml.application.operations.services import OperationService
from forgeml.application.package.services import PackageService
from forgeml.core.config import AppSettings
from forgeml.infrastructure.database.provider import DatabaseProvider
from forgeml.infrastructure.package.zip_archive import ZipArchiveReader
from forgeml.infrastructure.storage.artifact_store import FilesystemArtifactStore

API_PREFIX = "/v1"


class Container:
    """The dependency graph, wired once and shared by the routes."""

    def __init__(self, settings: AppSettings) -> None:
        self.database = DatabaseProvider(settings)
        self.packages = PackageService(
            unit_of_work=self.database.unit_of_work,
            store=FilesystemArtifactStore(settings.artifact_root),
            reader=ZipArchiveReader(),
            limits=settings.package_limits,
        )
        self.operations = OperationService(unit_of_work=self.database.unit_of_work)


def create_application(settings: AppSettings) -> FastAPI:
    """Create the control-plane application with its dependencies wired."""

    container = Container(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        # Docs 11: startup fails closed when the database is unavailable. The
        # recovery sweep both performs ADR-016's crash recovery and proves the
        # database answers, so one call satisfies both requirements.
        container.database.recover_orphaned_operations()
        yield
        container.database.dispose()

    app = FastAPI(
        title="ForgeML Control Plane",
        version=settings.service_version,
        docs_url=None,
        redoc_url=None,
        # The schema is published; the interactive explorers are not. Docs 11
        # keeps the control plane on an administrative network until an
        # authorization ADR exists, and a browsable console invites exactly the
        # exposure that decision has not yet been made.
        openapi_url=f"{API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )
    app.state.container = container

    register_error_handlers(app)
    app.include_router(
        create_health_router(settings, container.database.check_readiness)
    )
    app.include_router(create_package_router(container.packages), prefix=API_PREFIX)
    app.include_router(create_operation_router(container.operations), prefix=API_PREFIX)
    app.add_middleware(RequestContextMiddleware)
    return app
