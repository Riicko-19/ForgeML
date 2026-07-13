"""Application error invariant tests."""

from typing import cast

import pytest

from forgeml.core.errors import AppError, ErrorCategory, ErrorDetail


def test_valid_error_is_immutable_and_safe() -> None:
    detail = ErrorDetail(
        code="field_invalid",
        message="Field is invalid.",
        path=("items", 0, "name"),
    )
    error = AppError(
        category=ErrorCategory.VALIDATION,
        code="request_validation_failed",
        message="Request validation failed.",
        details=(detail,),
    )

    assert error.details == (detail,)
    with pytest.raises(AttributeError):
        attribute = "code"
        setattr(error, attribute, "changed")


@pytest.mark.parametrize(
    "code",
    ["", "UPPER", "1bad", "bad-hyphen", "a" * 65],
)
def test_invalid_codes_are_rejected(code: str) -> None:
    with pytest.raises(ValueError):
        ErrorDetail(code=code, message="Safe.")


@pytest.mark.parametrize("message", ["", "line\nbreak", "x" * 513])
def test_invalid_messages_are_rejected(message: str) -> None:
    with pytest.raises(ValueError):
        ErrorDetail(code="invalid", message=message)


@pytest.mark.parametrize(
    "path",
    [
        (True,),
        (-1,),
        (2_147_483_648,),
        ("",),
        ("x" * 129,),
        ("line\nbreak",),
        (object(),),
        tuple("x" for _ in range(33)),
    ],
)
def test_invalid_paths_are_rejected(path: tuple[object, ...]) -> None:
    with pytest.raises(ValueError):
        ErrorDetail(
            code="invalid",
            message="Invalid.",
            path=cast(tuple[str | int, ...], path),
        )


def test_detail_count_is_bounded() -> None:
    detail = ErrorDetail(code="invalid", message="Invalid.")

    with pytest.raises(ValueError, match="at most 100"):
        AppError(
            category=ErrorCategory.VALIDATION,
            code="invalid",
            message="Invalid.",
            details=tuple(detail for _ in range(101)),
        )


def test_details_must_be_typed() -> None:
    with pytest.raises(ValueError, match="ErrorDetail"):
        AppError(
            category=ErrorCategory.INTERNAL,
            code="internal_error",
            message="Unexpected.",
            details=cast(tuple[ErrorDetail, ...], ("not-a-detail",)),
        )
