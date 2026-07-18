"""FastAPI application composition root."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from forgeml.api.authentication import AuthenticationMiddleware
from forgeml.api.error_handlers import register_error_handlers
from forgeml.api.health import create_health_router
from forgeml.api.middleware import RequestContextMiddleware
from forgeml.api.v1.deployments import create_admin_router, create_deployment_router
from forgeml.api.v1.operations import create_operation_router
from forgeml.api.v1.packages import create_package_router
from forgeml.api.v1.predictions import create_prediction_router
from forgeml.application.deployment.services import DeploymentServices
from forgeml.application.identity.services import ApiKeyVerifier
from forgeml.application.operations.services import OperationService
from forgeml.application.package.services import PackageService
from forgeml.application.routing.services import RouteManager
from forgeml.core.config import AppSettings
from forgeml.domain.identity.ports import CredentialVerifier
from forgeml.infrastructure.database.provider import DatabaseProvider
from forgeml.infrastructure.package.zip_archive import ZipArchiveReader
from forgeml.infrastructure.runtime.docker import DockerRuntimeManager
from forgeml.infrastructure.runtime.http_gateway import HttpPredictionGateway
from forgeml.infrastructure.storage.artifact_store import FilesystemArtifactStore

API_PREFIX = "/v1"


class Container:
    """The dependency graph, wired once and shared by the routes."""

    def __init__(self, settings: AppSettings) -> None:
        self.database = DatabaseProvider(settings)
        store = FilesystemArtifactStore(settings.artifact_root)
        reader = ZipArchiveReader()
        self.packages = PackageService(
            unit_of_work=self.database.unit_of_work,
            store=store,
            reader=reader,
            limits=settings.package_limits,
        )
        self.operations = OperationService(unit_of_work=self.database.unit_of_work)
        # Epic 1: the credential verifier. ApiKeyVerifier is one implementation
        # of the CredentialVerifier port; a future JWT or OIDC verifier is
        # composed here and nothing above this line changes (ADR-024).
        self.verifier = ApiKeyVerifier(unit_of_work=self.database.unit_of_work)
        # Module 6: the real runtime. The Docker adapter resolves the package
        # archive through the same artifact store and reads its src/ into the
        # build context; nothing above the RuntimeManager port changes.
        runtime = DockerRuntimeManager(
            store=store, reader=reader, limits=settings.package_limits
        )
        # ForgeML 0.9: the deployment use cases are four services -- queries,
        # lifecycle, activation, reconciliation -- bundled here and wired once.
        self.deployments = DeploymentServices.create(
            unit_of_work=self.database.unit_of_work, runtime=runtime
        )
        # Module 7: the platform routing layer. RouteManager resolves the active
        # version through the deployment read model, health-checks through the
        # same runtime port, and forwards predictions through the HTTP gateway.
        # It never touches Docker directly.
        self.routing = RouteManager(
            deployments=self.deployments.queries,
            runtime=runtime,
            gateway=HttpPredictionGateway(),
        )


def create_application(
    settings: AppSettings, verifier: CredentialVerifier | None = None
) -> FastAPI:
    """Create the control-plane application with its dependencies wired.

    `verifier` is a composition seam, not a switch. It exists because ADR-024
    anticipates a JWT or OIDC verifier being composed here, and because tests
    that run without a metadata database still have to authenticate -- ADR-025
    left no bypass for them to disable. Passing None composes the real
    ApiKeyVerifier, which is what `bootstrap` does and the only thing a
    deployment can do: there is no setting, environment variable, or header
    that reaches this argument.
    """

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
    app.include_router(
        create_deployment_router(container.deployments), prefix=API_PREFIX
    )
    app.include_router(
        create_admin_router(container.deployments.reconciliation), prefix=API_PREFIX
    )
    app.include_router(create_prediction_router(container.routing), prefix=API_PREFIX)
    # Order matters. add_middleware prepends, so the last added is outermost:
    # request context wraps authentication, which means a 401 still carries a
    # server-owned request id and is still logged like any other response.
    app.add_middleware(
        AuthenticationMiddleware, verifier=verifier or container.verifier
    )
    app.add_middleware(RequestContextMiddleware)
    return app
