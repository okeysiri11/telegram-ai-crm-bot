"""Health monitoring — services, containers, queues, DB, integrations, AI models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class HealthMonitor:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def check(
        self,
        *,
        target: str,
        target_type: str = "service",
        status: str = "healthy",
        detail: str = "",
    ) -> dict[str, Any]:
        if not target:
            raise ValidationError("target required")
        st = status.lower().strip()
        if st not in ("healthy", "degraded", "unhealthy"):
            raise ValidationError("status must be healthy, degraded, or unhealthy")
        hid = _id("obs_hlth")
        return self.store.obs_health.save(
            hid,
            {
                "health_id": hid,
                "target": target,
                "target_type": target_type.lower(),
                "status": st,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        by = {"healthy": 0, "degraded": 0, "unhealthy": 0}
        for item in self.store.obs_health.list_all():
            if isinstance(item, dict):
                by[item.get("status", "healthy")] = by.get(item.get("status", "healthy"), 0) + 1
        return {"checks": self.store.obs_health.count(), "by_status": by}
