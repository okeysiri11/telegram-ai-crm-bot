"""Cost analytics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CostAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        total = 0.0
        by_agent: dict[str, float] = {}
        for exe in self.store.aop_executions.list_all():
            for step in exe.get("step_results") or []:
                cost = float(step.get("cost", 0) or 0)
                total += cost
                aid = step.get("agent_id") or "unassigned"
                by_agent[aid] = by_agent.get(aid, 0.0) + cost
        rid = _id("aop_cost")
        return self.store.aop_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "cost",
                "total_cost": total,
                "by_agent": by_agent,
                "at": _now(),
            },
        )
