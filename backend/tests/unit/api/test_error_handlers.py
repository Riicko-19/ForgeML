"""Direct error-mapping branch tests."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, cast

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from forgeml.api import error_handlers
from forgeml.core.correlation import reset_request_id, set_request_id
from forgeml.core.errors import AppError, ErrorCategory

Handler = Callable[[Request, Exception], Coroutine[Any, Any, JSONResponse]]


def _run_handler(handler: Handler, exc: Exception) -> JSONResponse:
    request = cast(Request, None)
    return asyncio.run(handler(request, exc))


@pytest.mark.parametrize(
    ("category", "status"),
    [
        (ErrorCategory.BAD_REQUEST, 400),
        (ErrorCategory.NOT_FOUND, 404),
        (ErrorCategory.CONFLICT, 409),
        (ErrorCategory.VALIDATION, 422),
        (ErrorCategory.POLICY_LIMIT, 429),
        (ErrorCategory.INTERNAL, 500),
        (ErrorCategory.UPSTREAM_FAILURE, 502),
        (ErrorCategory.DEPENDENCY_UNAVAILABLE, 503),
    ],
)
def test_all_application_categories_map(category: ErrorCategory, status: int) -> None:
    token = set_request_id("00000000-0000-4000-8000-000000000001")
    error = AppError(category=category, code="mapped_error", message="Mapped.")
    try:
        response = _run_handler(error_handlers.app_error_handler, error)
    finally:
        reset_request_id(token)

    assert response.status_code == status
    if status == 500:
        assert response.body == (
            b'{"code":"internal_error","message":"An unexpected error occurred.",'
            b'"request_id":"00000000-0000-4000-8000-000000000001"}'
        )


def test_mismatched_registered_handler_inputs_fail_safe() -> None:
    for handler in (
        error_handlers.app_error_handler,
        error_handlers.http_error_handler,
        error_handlers.validation_error_handler,
    ):
        response = _run_handler(handler, RuntimeError("secret"))
        assert response.status_code == 500


@pytest.mark.parametrize("status", [400, 418, 500, 503])
def test_unapproved_http_status_fails_safe(status: int) -> None:
    response = _run_handler(
        error_handlers.http_error_handler,
        HTTPException(status_code=status),
    )

    assert response.status_code == 500
    assert b'"code":"internal_error"' in response.body
    assert b"request_malformed" not in response.body


def test_validation_path_is_bounded_and_sanitized() -> None:
    location: tuple[object, ...] = (
        "body",
        True,
        -1,
        2_147_483_648,
        "",
        "x" * 129,
        "line\nbreak",
        object(),
        *tuple("valid" for _ in range(40)),
    )

    path = error_handlers._validation_path(location)

    assert path is not None
    assert len(path) == 32
    assert set(path) == {"valid"}


def test_non_json_validation_error_without_location_is_safe() -> None:
    error = RequestValidationError(
        [
            {
                "type": "missing",
                "loc": (),
                "msg": "secret",
                "input": "secret",
            }
        ]
    )
    response = _run_handler(error_handlers.validation_error_handler, error)

    assert response.status_code == 422
    assert b"secret" not in response.body
    assert b"path" not in response.body


def test_terminal_error_handlers_are_generic() -> None:
    assert (
        _run_handler(
            error_handlers.pydantic_error_handler, RuntimeError("secret")
        ).status_code
        == 500
    )
    assert (
        _run_handler(
            error_handlers.unexpected_error_handler, RuntimeError("secret")
        ).status_code
        == 500
    )
