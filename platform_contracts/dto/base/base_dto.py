"""Base DTO — Sprint 21.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str = "dto") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class BaseDTO:
    id: str = field(default_factory=lambda: _id("dto"))
    version: int = 1
    tenant_id: str | None = None
    organization_id: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseDTO":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})

    def touch(self) -> None:
        self.updated_at = _now()
