"""Request-local server correlation context."""

from __future__ import annotations

from contextvars import ContextVar, Token
from uuid import uuid4

_request_id: ContextVar[str | None] = ContextVar("forgeml_request_id", default=None)


def new_request_id() -> str:
    """Create a canonical server-owned request identifier."""

    return str(uuid4())


def set_request_id(request_id: str) -> Token[str | None]:
    """Set a request identifier and return the reset token."""

    return _request_id.set(request_id)


def current_request_id() -> str | None:
    """Return the current request identifier, if inside a request."""

    return _request_id.get()


def reset_request_id(token: Token[str | None]) -> None:
    """Restore correlation context using its exact token."""

    _request_id.reset(token)
