"""Base event contract — Sprint 21.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BaseEvent:
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    event_type: str = "domain.unknown"
    aggregate_id: str = ""
    aggregate_type: str = ""
    source_service: str = "enterprise_hub"
    actor: str = "system"
    payload: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1
    timestamp: str = field(default_factory=_now)
    trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseEvent":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})
