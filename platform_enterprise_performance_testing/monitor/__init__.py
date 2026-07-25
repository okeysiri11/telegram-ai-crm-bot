"""Resource Monitor — Sprint 25.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_performance_testing.models import RESOURCE_METRICS


class ResourceMonitor:
    def snapshot(self, *, load_users: int = 0) -> dict[str, Any]:
        load_users = int(load_users)
        base = 20 + load_users / 100
        metrics = {
            "cpu": round(min(99.0, base + 10), 2),
            "ram": round(min(99.0, base + 5), 2),
            "disk": round(min(90.0, 30 + load_users / 500), 2),
            "network": round(min(95.0, 15 + load_users / 80), 2),
            "database": round(min(98.0, 18 + load_users / 70), 2),
            "redis": round(min(90.0, 10 + load_users / 200), 2),
            "event_bus": round(min(95.0, 12 + load_users / 150), 2),
            "ai_providers": round(min(97.0, 25 + load_users / 120), 2),
        }
        return {"metrics": metrics, "tracked": list(RESOURCE_METRICS), "load_users": load_users}
