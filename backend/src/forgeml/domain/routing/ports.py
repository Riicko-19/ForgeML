"""Ports the routing module drives (docs 04, ADR-005/ADR-010).

`PredictionGateway` is the provider-neutral boundary in front of the runtime's
HTTP prediction endpoint. It exists so the route manager can forward a
prediction to a running container without knowing that the transport is HTTP or
that the runtime is Docker -- the same reason `RuntimeManager` fronts the
lifecycle. The frozen `RuntimeManager` contract is unchanged: forwarding a
prediction is a distinct concern with its own port, not a new lifecycle
primitive.

`ActiveTarget` is what resolving a deployment's route yields: the internal
endpoint to forward to, the container to health-check, and the schemas the
request and response must satisfy.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ActiveTarget:
    """The resolved routing target for a deployment's active version."""

    endpoint: str
    container_id: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any]


class PredictionUnavailable(Exception):
    """The runtime could not be reached. Maps to 503 deployment_unavailable."""


class PredictionUpstreamError(Exception):
    """The runtime failed, timed out, or returned an unusable response.

    Maps to 502 prediction_runtime_failed; the detail stays in protected logs
    (docs 12), never on the wire.
    """


class PredictionGateway(Protocol):
    """Forward one prediction to a runtime's internal endpoint (ADR-010)."""

    def predict(self, endpoint: str, payload: Any) -> Any:
        """POST the payload to the endpoint's prediction route and return the
        decoded response body. Raise PredictionUnavailable if the runtime cannot
        be reached, PredictionUpstreamError if it fails or times out."""
