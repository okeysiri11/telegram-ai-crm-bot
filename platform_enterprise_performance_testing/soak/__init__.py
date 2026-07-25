"""Soak Test Engine — Sprint 25.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_performance_testing.models import SOAK_DURATIONS_HOURS


class SoakTestEngine:
    def run(self, *, hours: int = 1, users: int = 100) -> dict[str, Any]:
        hours = int(hours)
        if hours not in SOAK_DURATIONS_HOURS:
            raise ValueError(f"unsupported soak duration: {hours}")
        # synthetic drift
        mem_growth_mb = round(hours * 2.5, 2)
        error_accumulation = round(hours * 0.001, 4)
        latency_drift_ms = round(hours * 1.2, 2)
        return {
            "engine": "soak",
            "hours": hours,
            "users": int(users),
            "memory_leak_mb": mem_growth_mb,
            "error_accumulation": error_accumulation,
            "performance_degradation_ms": latency_drift_ms,
            "connection_stability": mem_growth_mb < 50,
            "stable": mem_growth_mb < 40 and error_accumulation < 0.05,
            "supported_durations_hours": list(SOAK_DURATIONS_HOURS),
        }
