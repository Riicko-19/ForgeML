"""Provider-neutral application error contracts."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_MAX_MESSAGE = 512
_MAX_DETAILS = 100
_MAX_PATH = 32
_MAX_PATH_STRING = 128
_MAX_PATH_INTEGER = 2_147_483_647


class ErrorCategory(StrEnum):
    """Transport-neutral classes of expected application failure."""

    BAD_REQUEST = "bad_request"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    VALIDATION = "validation"
    POLICY_LIMIT = "policy_limit"
    UPSTREAM_FAILURE = "upstream_failure"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    INTERNAL = "internal"


def _validate_code(code: str) -> None:
    if not _CODE_PATTERN.fullmatch(code):
        raise ValueError(
            "error code must be lower snake case and at most 64 characters"
        )


def _validate_message(message: str) -> None:
    if not 1 <= len(message) <= _MAX_MESSAGE:
        raise ValueError("error message must contain 1 to 512 characters")
    if any(unicodedata.category(character).startswith("C") for character in message):
        raise ValueError("error message must not contain control characters")


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    """A bounded, safe detail for an expected application error."""

    code: str
    message: str
    path: tuple[str | int, ...] | None = None

    def __post_init__(self) -> None:
        _validate_code(self.code)
        _validate_message(self.message)
        if self.path is None:
            return
        if len(self.path) > _MAX_PATH:
            raise ValueError("error path must contain at most 32 segments")
        for segment in self.path:
            if isinstance(segment, bool):
                raise ValueError("boolean path segments are not allowed")
            if isinstance(segment, int):
                if not 0 <= segment <= _MAX_PATH_INTEGER:
                    raise ValueError("integer path segment is out of range")
            elif isinstance(segment, str):
                if not 1 <= len(segment) <= _MAX_PATH_STRING:
                    raise ValueError("string path segment is out of range")
                if any(
                    unicodedata.category(character).startswith("C")
                    for character in segment
                ):
                    raise ValueError("string path segment contains a control character")
            else:
                raise ValueError("unsupported path segment type")


@dataclass(frozen=True, slots=True)
class AppError(Exception):
    """An immutable expected application failure."""

    category: ErrorCategory
    code: str
    message: str
    details: tuple[ErrorDetail, ...] = ()

    def __post_init__(self) -> None:
        _validate_code(self.code)
        _validate_message(self.message)
        if len(self.details) > _MAX_DETAILS:
            raise ValueError("an error may contain at most 100 details")
        if not all(isinstance(detail, ErrorDetail) for detail in self.details):
            raise ValueError("details must contain ErrorDetail values")
        Exception.__init__(self, self.message)
