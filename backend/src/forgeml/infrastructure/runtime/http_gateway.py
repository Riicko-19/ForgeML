"""HTTP prediction gateway: the real `PredictionGateway` (ADR-010).

Forwards a prediction to a runtime container's internal `/predict` endpoint over
HTTP. It uses the standard library rather than an HTTP client dependency, for the
same reason the runtime adapter shells out to the Docker CLI: the transport is
simple and adding a pinned runtime dependency is not worth it. The control plane
reaches the runtime on the internal Docker network (ADR-010); the endpoint is
never a client-supplied URL, so only the platform's own internal targets are
opened here.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from forgeml.domain.routing.ports import (
    PredictionUnavailable,
    PredictionUpstreamError,
)

_DEFAULT_TIMEOUT_SECONDS = 30.0


class HttpPredictionGateway:
    """POSTs a prediction to a runtime's internal endpoint over HTTP."""

    def __init__(self, timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout_seconds

    def predict(self, endpoint: str, payload: Any) -> Any:
        url = f"{endpoint.rstrip('/')}/predict"
        request = (
            Request(  # noqa: S310 - platform-internal endpoint, never client input
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:  # noqa: S310
                raw = response.read()
        except HTTPError as error:  # the runtime answered with a non-2xx status
            raise PredictionUpstreamError("the runtime returned an error") from error
        except TimeoutError as error:
            raise PredictionUpstreamError("the runtime timed out") from error
        except (URLError, OSError) as error:  # could not reach the runtime at all
            raise PredictionUnavailable("the runtime is unreachable") from error
        try:
            return json.loads(raw)
        except (ValueError, UnicodeDecodeError) as error:
            raise PredictionUpstreamError(
                "the runtime response was unreadable"
            ) from error
