"""Audit events (docs 04: append-only; no payloads, no secrets)."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

MAX_METADATA_ENTRIES = 32
_MAX_KEY = 64
_MAX_VALUE = 256
_MAX_ACTION = 64
_MAX_TARGET = 128


class ActorType(StrEnum):
    """Who caused a state change."""

    OPERATOR = "operator"
    SYSTEM = "system"


def _safe_text(value: str, limit: int, label: str) -> str:
    if not 1 <= len(value) <= limit:
        raise ValueError(f"{label} must contain 1 to {limit} characters")
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ValueError(f"{label} must not contain control characters")
    return value


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """One append-only record of a state change.

    Metadata is bounded and redacted by construction: an audit row may describe
    what changed, never the content that changed.

    `id` and `occurred_at` are assigned by the database on append, so they are
    absent when an event is written and present when one is read back. Docs 04
    requires both on the record; an audit trail that cannot be ordered in time
    is not a trail.
    """

    actor_type: ActorType
    action: str
    target_type: str
    target_id: str
    correlation_id: UUID
    metadata: dict[str, str] = field(default_factory=dict)
    id: UUID | None = None
    occurred_at: datetime | None = None

    def __post_init__(self) -> None:
        _safe_text(self.action, _MAX_ACTION, "action")
        _safe_text(self.target_type, _MAX_TARGET, "target_type")
        _safe_text(self.target_id, _MAX_TARGET, "target_id")
        if len(self.metadata) > MAX_METADATA_ENTRIES:
            raise ValueError(
                f"an audit event may carry at most {MAX_METADATA_ENTRIES} metadata keys"
            )
        for key, value in self.metadata.items():
            _safe_text(key, _MAX_KEY, "metadata key")
            _safe_text(value, _MAX_VALUE, "metadata value")
