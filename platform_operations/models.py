# Operations dashboard domain models — widget envelopes and shared context.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

WidgetStatus = Literal["ok", "degraded", "error", "cached"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WidgetMeta:
    widget_id: str
    updated_at: str
    refresh_interval: int
    status: WidgetStatus = "ok"
    cache_hit: bool = False
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "widget_id": self.widget_id,
            "updated_at": self.updated_at,
            "refresh_interval": self.refresh_interval,
            "status": self.status,
            "cache_hit": self.cache_hit,
            "duration_ms": self.duration_ms,
        }


@dataclass
class WidgetPayload:
    meta: WidgetMeta
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"meta": self.meta.to_dict(), "data": self.data}


@dataclass
class DashboardPayload:
    generated_at: str
    widgets: dict[str, WidgetPayload]
    duration_ms: float = 0.0
    cache_hit: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "duration_ms": self.duration_ms,
            "cache_hit": self.cache_hit,
            "widgets": {key: widget.to_dict() for key, widget in self.widgets.items()},
        }


@dataclass
class SharedDashboardContext:
    """Shared fetch results to avoid duplicate service calls within one request."""

    system_info: dict[str, Any] | None = None
    health: dict[str, Any] | None = None
    sla_stats: dict[str, Any] | None = None
    pool_dashboard: dict[str, Any] | None = None
    workflow_stats: dict[str, Any] | None = None
    assignment_stats: dict[str, Any] | None = None
    kpi_day: dict[str, Any] | None = None
    kpi_week: dict[str, Any] | None = None
    kpi_month: dict[str, Any] | None = None
    event_bus: dict[str, Any] | None = None
    recent_audit: list[dict[str, Any]] = field(default_factory=list)
    config_changes: list[dict[str, Any]] = field(default_factory=list)
