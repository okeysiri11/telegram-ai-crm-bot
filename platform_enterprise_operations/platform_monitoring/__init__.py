"""Platform Monitoring — Sprint 23.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_operations.models import MONITOR_TARGETS


class PlatformMonitoring:
    def snapshot(self, *, statuses: dict[str, str] | None = None) -> dict[str, Any]:
        statuses = dict(statuses or {})
        targets = {}
        for t in MONITOR_TARGETS:
            targets[t] = statuses.get(t, "ok")
        degraded = [k for k, v in targets.items() if v != "ok"]
        return {
            "targets": targets,
            "degraded": degraded,
            "all_ok": len(degraded) == 0,
            "observability_ref": "enterprise_observability",
        }
