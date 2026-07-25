"""Load Test Engine — Sprint 25.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_performance_testing.models import LOAD_USER_LEVELS


class LoadTestEngine:
    def run(self, *, users: int, base_latency_ms: float = 50.0) -> dict[str, Any]:
        users = int(users)
        if users not in LOAD_USER_LEVELS:
            raise ValueError(f"unsupported user level: {users}; allowed={LOAD_USER_LEVELS}")
        # synthetic curve: latency grows with concurrency
        factor = users / 100.0
        avg = round(base_latency_ms * (1 + factor * 0.15), 2)
        throughput = round(max(1.0, users * 10 / max(avg / 50, 1)), 2)
        error_rate = round(min(0.2, max(0.0, (users - 1000) / 20000)), 4)
        return {
            "engine": "load",
            "users": users,
            "response_time_ms": avg,
            "throughput_rps": throughput,
            "error_rate": error_rate,
            "cpu_pct": round(min(98.0, 20 + users / 60), 2),
            "ram_pct": round(min(95.0, 25 + users / 80), 2),
            "database_usage_pct": round(min(97.0, 15 + users / 70), 2),
            "network_mbps": round(users * 0.05, 2),
            "supported_levels": list(LOAD_USER_LEVELS),
        }
