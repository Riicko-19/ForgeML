"""Platform prediction routing (docs 04/12; ADR-005/ADR-010).

The route manager is the only thing between a client and a model: the client
speaks to ForgeML, never to a runtime container. It resolves a deployment's one
active version through the deployment service, confirms the runtime is healthy
through the runtime manager, forwards the request through the prediction gateway,
and maps every failure to a platform error that leaks no runtime topology.

It is provider-independent by construction: it depends on the `RuntimeManager`
and `PredictionGateway` ports and the deployment service, never on Docker.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from jsonschema import Draft202012Validator

from forgeml.application.deployment.services import DeploymentService
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.deployment.ports import RuntimeManager, RuntimeUnavailable
from forgeml.domain.routing.ports import (
    PredictionGateway,
    PredictionUnavailable,
    PredictionUpstreamError,
)


class RouteManager:
    """Resolves the active version and proxies a prediction to its runtime."""

    def __init__(
        self,
        deployments: DeploymentService,
        runtime: RuntimeManager,
        gateway: PredictionGateway,
    ) -> None:
        self._deployments = deployments
        self._runtime = runtime
        self._gateway = gateway

    def predict(self, name: str, payload: Any, correlation_id: UUID) -> Any:
        """Forward one prediction to the deployment's active version."""

        target = self._deployments.resolve_active_target(name)
        if target is None:
            raise _unavailable()

        message = _schema_error(payload, target.input_schema)
        if message is not None:
            raise _input_invalid(message)

        # docs 12: a prediction only reaches a runtime that is actually healthy.
        # ponytail: this inspects the runtime per request; a cached readiness
        # gate (Module 8 monitoring) would remove the per-prediction cost.
        try:
            status = self._runtime.inspect(target.container_id)
        except RuntimeUnavailable as error:
            raise _unavailable() from error
        if not (status.present and status.running and status.healthy):
            raise _unavailable()

        try:
            body = self._gateway.predict(target.endpoint, payload)
        except PredictionUnavailable as error:
            raise _unavailable() from error
        except PredictionUpstreamError as error:
            raise _runtime_failed() from error

        result = body.get("result") if isinstance(body, dict) else None
        if result is None or _schema_error(result, target.output_schema) is not None:
            raise _runtime_failed()
        return result


def _schema_error(instance: Any, schema: Any) -> str | None:
    error = next(iter(Draft202012Validator(schema).iter_errors(instance)), None)
    return error.message if error is not None else None


def _unavailable() -> AppError:
    return AppError(
        category=ErrorCategory.DEPENDENCY_UNAVAILABLE,
        code="deployment_unavailable",
        message="the deployment has no active healthy runtime to serve predictions",
    )


def _input_invalid(message: str) -> AppError:
    return AppError(
        category=ErrorCategory.VALIDATION,
        code="prediction_input_invalid",
        message=f"the prediction input does not match the model schema: {message}"[
            :512
        ],
    )


def _runtime_failed() -> AppError:
    # Opaque by design (docs 12): the model's own error stays in protected logs.
    return AppError(
        category=ErrorCategory.UPSTREAM_FAILURE,
        code="prediction_runtime_failed",
        message="the model runtime failed to produce a valid prediction",
    )
