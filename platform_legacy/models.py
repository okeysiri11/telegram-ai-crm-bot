# Legacy boundary models — call traces and migration statistics.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class LegacyCallRecord:
    adapter: str
    method: str
    caller: str
    success: bool
    latency_ms: float
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None


@dataclass(slots=True)
class LegacyMetrics:
    total_calls: int = 0
    total_errors: int = 0
    calls_by_adapter: dict[str, int] = field(default_factory=dict)
    errors_by_adapter: dict[str, int] = field(default_factory=dict)
    deprecated_api_hits: dict[str, int] = field(default_factory=dict)
    recent_calls: list[LegacyCallRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "calls_by_adapter": dict(self.calls_by_adapter),
            "errors_by_adapter": dict(self.errors_by_adapter),
            "deprecated_api_hits": dict(self.deprecated_api_hits),
            "recent_calls": [
                {
                    "adapter": c.adapter,
                    "method": c.method,
                    "caller": c.caller,
                    "success": c.success,
                    "latency_ms": c.latency_ms,
                    "occurred_at": c.occurred_at.isoformat(),
                    "error": c.error,
                }
                for c in self.recent_calls[-50:]
            ],
        }


@dataclass(slots=True)
class MigrationProgress:
    registered_adapters: list[str] = field(default_factory=list)
    wired_adapters: list[str] = field(default_factory=list)
    pending_replacements: list[str] = field(default_factory=list)
    isolation_enforced: bool = True

    def to_dict(self) -> dict[str, Any]:
        total = len(self.registered_adapters) or 1
        migrated = len(self.wired_adapters)
        return {
            "registered_adapters": list(self.registered_adapters),
            "wired_adapters": list(self.wired_adapters),
            "pending_replacements": list(self.pending_replacements),
            "isolation_enforced": self.isolation_enforced,
            "migration_percent": round(migrated / total * 100, 1),
        }
