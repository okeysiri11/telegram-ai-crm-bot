"""Stress Test Engine — Sprint 25.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_performance_testing.models import STRESS_LIMITS


class StressTestEngine:
    def run(self, *, start_users: int = 100, step: int = 200, max_users: int = 5000) -> dict[str, Any]:
        start_users = int(start_users)
        step = max(1, int(step))
        max_users = int(max_users)
        points = []
        degradation_at = None
        for users in range(start_users, max_users + 1, step):
            error_rate = round(min(1.0, max(0.0, (users - 800) / 4000)), 4)
            latency = round(40 + users * 0.08, 2)
            degraded = error_rate >= 0.05 or latency > 500
            points.append({"users": users, "error_rate": error_rate, "latency_ms": latency, "degraded": degraded})
            if degraded and degradation_at is None:
                degradation_at = users
        limits = {name: {"limit_users": (degradation_at or max_users), "status": "found" if degradation_at else "not_reached"} for name in STRESS_LIMITS}
        return {
            "engine": "stress",
            "points": points[-20:],
            "degradation_point_users": degradation_at,
            "limits": limits,
            "pushed_to_failure": degradation_at is not None,
        }
