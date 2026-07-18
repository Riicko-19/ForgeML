"""Request-local authenticated identity.

Mirrors `correlation.py` deliberately: the API layer establishes the value once
per request and the routers read it, exactly as they already do for the request
id. The contextvar is a transport detail and stops at the API boundary --
application services receive a `Principal` as an argument (ADR-019), never by
reaching in here. Nothing outside `forgeml.api` reads this module.

The default is `None`, and `None` is meaningful: it is what an unauthenticated
route has (ADR-023). There is no anonymous principal to fall back to.
"""

from __future__ import annotations

from contextvars import ContextVar, Token

from forgeml.domain.identity.models import AuthenticationContext

_authentication: ContextVar[AuthenticationContext | None] = ContextVar(
    "forgeml_authentication", default=None
)


def set_authentication(
    context: AuthenticationContext,
) -> Token[AuthenticationContext | None]:
    """Bind the authenticated identity for this request; returns the reset token."""

    return _authentication.set(context)


def current_authentication() -> AuthenticationContext | None:
    """The authenticated identity, or None outside an authenticated request."""

    return _authentication.get()


def reset_authentication(token: Token[AuthenticationContext | None]) -> None:
    """Restore the previous context using its exact token."""

    _authentication.reset(token)
