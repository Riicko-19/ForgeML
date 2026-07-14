"""Domain records for the metadata layer."""

from __future__ import annotations

from uuid import uuid4

import pytest

from forgeml.domain.audit.models import MAX_METADATA_ENTRIES, ActorType, AuditEvent
from forgeml.domain.operations.models import OperationState
from forgeml.domain.package.models import PackageState, ValidationState


def event(**overrides: object) -> AuditEvent:
    fields: dict[str, object] = {
        "actor_type": ActorType.OPERATOR,
        "action": "package.validated",
        "target_type": "package",
        "target_id": "a" * 64,
        "correlation_id": uuid4(),
    }
    fields.update(overrides)
    return AuditEvent(**fields)  # type: ignore[arg-type]


def test_only_succeeded_and_failed_are_terminal() -> None:
    assert OperationState.SUCCEEDED.is_terminal
    assert OperationState.FAILED.is_terminal
    assert not OperationState.PENDING.is_terminal
    assert not OperationState.RUNNING.is_terminal


def test_a_validation_verdict_maps_onto_the_package_lifecycle() -> None:
    assert (
        PackageState.from_validation(ValidationState.VALIDATED)
        is PackageState.VALIDATED
    )
    assert (
        PackageState.from_validation(ValidationState.REJECTED) is PackageState.REJECTED
    )


def test_a_well_formed_audit_event_is_accepted() -> None:
    assert event(metadata={"state": "validated"}).action == "package.validated"


@pytest.mark.parametrize(
    "overrides",
    [
        {"action": ""},
        {"action": "x" * 65},
        {"action": "package\nvalidated"},
        {"target_type": "pack\x00age"},
        {"target_id": ""},
    ],
)
def test_unsafe_audit_text_is_refused(overrides: dict[str, object]) -> None:
    # An audit trail is read by operators and shipped to log sinks. A control
    # character here is a forged log line there.
    with pytest.raises(ValueError, match="must"):
        event(**overrides)


def test_audit_metadata_is_bounded() -> None:
    with pytest.raises(ValueError, match="at most"):
        event(metadata={f"k{index}": "v" for index in range(MAX_METADATA_ENTRIES + 1)})


@pytest.mark.parametrize(
    "metadata",
    [{"key": ""}, {"key": "v" * 257}, {"": "value"}, {"key": "line\nbreak"}],
)
def test_unsafe_audit_metadata_is_refused(metadata: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="must"):
        event(metadata=metadata)
