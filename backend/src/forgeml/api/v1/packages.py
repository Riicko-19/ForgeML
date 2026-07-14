"""Package routes (docs 12)."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, File, Header, Query, Response, UploadFile, status

from forgeml.api.schemas import ErrorEnvelope
from forgeml.api.v1.schemas import (
    DEFAULT_PAGE_SIZE,
    Cursor,
    IdempotencyKey,
    OperationResource,
    PackageListResponse,
    PackageResource,
    PackageSummary,
    PageLimit,
    decode_cursor,
    encode_cursor,
)
from forgeml.application.package.services import PackageService
from forgeml.core.correlation import current_request_id, new_request_id
from forgeml.core.errors import AppError, ErrorCategory

_ERRORS: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorEnvelope},
    404: {"model": ErrorEnvelope},
    409: {"model": ErrorEnvelope},
    422: {"model": ErrorEnvelope},
    500: {"model": ErrorEnvelope},
    503: {"model": ErrorEnvelope},
}

MAX_FILENAME = 512


def _correlation_id() -> UUID:
    # ADR-015: the server owns this identifier. The middleware has already
    # generated it for this request; an inbound value is never trusted.
    return UUID(current_request_id() or new_request_id())


def _safe_filename(upload: UploadFile) -> str:
    """The client-supplied name, reduced to something safe to store and echo.

    A filename is untrusted text that ends up in a database row and an audit
    event. It never reaches the filesystem -- artifacts are addressed by
    checksum -- but it must not carry a path or a control character.
    """

    raw = (upload.filename or "package.forge").strip()
    leaf = raw.replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = "".join(character for character in leaf if character.isprintable())
    return cleaned[:MAX_FILENAME] or "package.forge"


def create_package_router(service: PackageService) -> APIRouter:
    """Create the package routes bound to the package use cases."""

    router = APIRouter(prefix="/packages", tags=["packages"])

    @router.post(
        "",
        response_model=OperationResource,
        status_code=status.HTTP_202_ACCEPTED,
        responses=_ERRORS,
        summary="Upload a .forge package and begin validation",
    )
    def upload_package(
        response: Response,
        file: Annotated[UploadFile, File()],
        idempotency_key: Annotated[IdempotencyKey | None, Header()] = None,
    ) -> OperationResource:
        if idempotency_key is None:
            # Docs 04: every mutating request carries a key. Without one a retry
            # after a dropped response would upload and validate a second time.
            raise AppError(
                category=ErrorCategory.BAD_REQUEST,
                code="idempotency_key_required",
                message="An Idempotency-Key header is required.",
            )

        operation = service.upload(
            stream=file.file,
            filename=_safe_filename(file),
            idempotency_key=idempotency_key,
            correlation_id=_correlation_id(),
        )
        response.headers["Location"] = f"/v1/operations/{operation.id}"
        return OperationResource.of(operation)

    @router.get(
        "",
        response_model=PackageListResponse,
        responses=_ERRORS,
        summary="List packages, newest first",
    )
    def list_packages(
        limit: Annotated[PageLimit, Query()] = DEFAULT_PAGE_SIZE,
        cursor: Annotated[Cursor | None, Query()] = None,
    ) -> PackageListResponse:
        page = service.list(limit=limit, cursor=decode_cursor(cursor))
        return PackageListResponse(
            items=tuple(PackageSummary.of(item) for item in page.items),
            next_cursor=encode_cursor(page.next_cursor),
        )

    @router.get(
        "/{package_id}",
        response_model=PackageResource,
        responses=_ERRORS,
        summary="Read one package with its validation findings",
    )
    def read_package(package_id: UUID) -> PackageResource:
        return PackageResource.of(service.get(package_id))

    return router
