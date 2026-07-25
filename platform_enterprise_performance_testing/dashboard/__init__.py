"""Performance Dashboard — Sprint 25.2."""

from __future__ import annotations

from typing import Any


class PerformanceTestingDashboard:
    def render(
        self,
        *,
        live_load: int = 0,
        active_users: int = 0,
        rps: float = 0.0,
        api: dict[str, Any] | None = None,
        database: dict[str, Any] | None = None,
        ai: dict[str, Any] | None = None,
        resources: dict[str, float] | None = None,
        errors: float = 0.0,
        bottlenecks: list[dict[str, Any]] | None = None,
        recommendations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        resources = dict(resources or {})
        return {
            "live_load": int(live_load),
            "active_users": int(active_users),
            "requests_per_sec": float(rps),
            "api_performance": dict(api or {}),
            "database": dict(database or {}),
            "ai_performance": dict(ai or {}),
            "cpu": resources.get("cpu"),
            "ram": resources.get("ram"),
            "errors": float(errors),
            "bottlenecks": list(bottlenecks or []),
            "recommendations": list(recommendations or []),
            "ci_cd_required": True,
        }
