"""ProductivityAnalytics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ProductivityAnalytics:
    kind = "productivity"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        tasks = self.store.aios_tasks.list_all()
        executions = self.store.aios_executions.list_all()
        completed = [t for t in tasks if t.get("state") == "completed"]
        failed = [t for t in tasks if t.get("state") == "failed"]
        running = [t for t in tasks if t.get("state") == "running"]
        spent = sum(float(e.get("spent", 0) or 0) for e in executions)
        aid = _id("aios_an")
        success = (len(completed) / len(tasks)) if tasks else 1.0
        payload: dict[str, Any] = {
            "analytics_id": aid,
            "kind": self.kind,
            "active_tasks": len(running),
            "completed_tasks": len(completed),
            "failed_tasks": len(failed),
            "success_rate": success,
            "total_cost": spent,
            "at": _now(),
        }
        if self.kind == "productivity":
            payload["throughput"] = len(completed)
        elif self.kind == "efficiency":
            payload["avg_cost"] = (spent / len(executions)) if executions else 0.0
            payload["bottlenecks"] = [t["task_id"] for t in tasks if t.get("state") == "blocked"]
        else:
            payload["recommendations"] = (
                ["reduce parallel fan-out when budget tight"] if spent > 1 else ["scale collaborative mode"]
            )
        return self.store.aios_analytics.save(aid, payload)
