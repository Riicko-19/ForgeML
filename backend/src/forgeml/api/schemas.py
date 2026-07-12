"""Frozen Module 0 HTTP response schemas."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ErrorCode = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")]
SafeMessage = Annotated[str, Field(min_length=1, max_length=512)]
PathString = Annotated[str, Field(min_length=1, max_length=128)]
PathInteger = Annotated[int, Field(ge=0, le=2_147_483_647)]
ServiceVersion = Annotated[
    str,
    Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9.+!-]+$"),
]


class ErrorDetailResponse(BaseModel):
    """Safe, bounded validation detail."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: ErrorCode
    message: SafeMessage
    path: (
        Annotated[
            tuple[PathString | PathInteger, ...],
            Field(max_length=32),
        ]
        | None
    ) = None


class ErrorEnvelope(BaseModel):
    """Common ForgeML HTTP error body."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: ErrorCode
    message: SafeMessage
    request_id: UUID
    details: (
        Annotated[
            tuple[ErrorDetailResponse, ...],
            Field(min_length=1, max_length=100),
        ]
        | None
    ) = None


class HealthResponse(BaseModel):
    """Operational health response."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok", "ready"]
    service: Literal["forgeml-control-plane"]
    version: ServiceVersion
