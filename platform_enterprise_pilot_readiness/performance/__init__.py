"""Performance Audit — Sprint 23.1."""

from __future__ import annotations

from typing import Any


class PerformanceAudit:
    def audit(self, *, timings: dict[str, float] | None = None) -> dict[str, Any]:
        timings = dict(timings or {})
        defaults = {
            "screen_open_ms": 400,
            "search_ms": 250,
            "booking_ms": 800,
            "dashboard_load_ms": 600,
        }
        measured = {k: float(timings.get(k, v)) for k, v in defaults.items()}
        bottlenecks = [k for k, v in measured.items() if v > 1000]
        return {
            "timings": measured,
            "bottlenecks": bottlenecks,
            "critical": len(bottlenecks) == 0,
            "within_budget": all(v < 2000 for v in measured.values()),
        }
