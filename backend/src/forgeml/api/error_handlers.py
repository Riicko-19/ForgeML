"""Safe HTTP error mapping for the control-plane boundary."""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from typing import Final
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from forgeml.api.schemas import ErrorDetailResponse, ErrorEnvelope
from forgeml.core.correlation import current_request_id, new_request_id
from forgeml.core.errors import AppError, ErrorCategory, ErrorDetail

_CATEGORY_STATUS: Final = {
    ErrorCategory.BAD_REQUEST: 400,
    ErrorCategory.NOT_FOUND: 404,
    ErrorCategory.CONFLICT: 409,
    ErrorCategory.VALIDATION: 422,
    ErrorCategory.POLICY_LIMIT: 429,
    ErrorCategory.INTERNAL: 500,
    ErrorCategory.UPSTREAM_FAILURE: 502,
    ErrorCategory.DEPENDENCY_UNAVAILABLE: 503,
}

_FRAMEWORK_ERRORS: Final = {
    404: ("route_not_found", "Resource not found."),
    405: ("method_not_allowed", "Method not allowed."),
}


def _request_id() -> str:
    return current_request_id() or new_request_id()


def _detail_response(detail: ErrorDetail) -> ErrorDetailResponse:
    return ErrorDetailResponse(
        code=detail.code,
        message=detail.message,
        path=detail.path,
    )


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: Sequence[ErrorDetailResponse] = (),
) -> JSONResponse:
    """Build the frozen FEK error envelope."""

    envelope = ErrorEnvelope(
        code=code,
        message=message,
        request_id=UUID(_request_id()),
        details=tuple(details) or None,
    )
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(mode="json", exclude_none=True),
    )


async def app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """Map an expected application error without provider details."""

    if not isinstance(exc, AppError):
        return internal_error_response()
    status_code = _CATEGORY_STATUS.get(exc.category, 500)
    if status_code == 500:
        return internal_error_response()
    return error_response(
        status_code=status_code,
        code=exc.code,
        message=exc.message,
        details=tuple(_detail_response(detail) for detail in exc.details),
    )


async def http_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """Normalize framework route and method failures."""

    if not isinstance(exc, HTTPException):
        return internal_error_response()
    mapping = _FRAMEWORK_ERRORS.get(exc.status_code)
    if mapping is None:
        return internal_error_response()
    code, message = mapping
    return error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
    )


def _validation_path(location: tuple[object, ...]) -> tuple[str | int, ...] | None:
    segments: list[str | int] = []
    for item in location:
        if item in {"body", "query", "path", "header", "cookie"}:
            continue
        if isinstance(item, bool):
            continue
        if (isinstance(item, int) and 0 <= item <= 2_147_483_647) or (
            isinstance(item, str)
            and 1 <= len(item) <= 128
            and not any(
                unicodedata.category(character).startswith("C") for character in item
            )
        ):
            segments.append(item)
        if len(segments) == 32:
            break
    return tuple(segments) or None


async def validation_error_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    """Normalize malformed JSON and request-schema failures."""

    if not isinstance(exc, RequestValidationError):
        return internal_error_response()
    errors = exc.errors()
    if any(item.get("type") == "json_invalid" for item in errors):
        return error_response(
            status_code=400,
            code="request_malformed",
            message="Request is malformed.",
        )

    details = tuple(
        ErrorDetailResponse(
            code="request_validation_error",
            message="Request field is invalid.",
            path=_validation_path(tuple(item.get("loc", ()))),
        )
        for item in errors[:100]
    )
    return error_response(
        status_code=422,
        code="request_validation_failed",
        message="Request validation failed.",
        details=details,
    )


async def pydantic_error_handler(_: Request, __: Exception) -> JSONResponse:
    """Prevent response-model validation details from reaching clients."""

    return error_response(
        status_code=500,
        code="internal_error",
        message="An unexpected error occurred.",
    )


async def unexpected_error_handler(_: Request, __: Exception) -> JSONResponse:
    """Last-resort safe HTTP failure."""

    return internal_error_response()


def internal_error_response() -> JSONResponse:
    """Create the generic unexpected-failure response."""

    return error_response(
        status_code=500,
        code="internal_error",
        message="An unexpected error occurred.",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all Module 0 error mappings."""

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(ValidationError, pydantic_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
