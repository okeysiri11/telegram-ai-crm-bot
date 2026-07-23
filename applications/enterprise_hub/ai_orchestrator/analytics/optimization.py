"""Optimization recommendations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class OptimizationEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def recommend(self) -> dict[str, Any]:
        agents = sorted(
            self.store.aop_agents.list_all(),
            key=lambda a: (a.get("cost_per_task", 0), a.get("load", 0)),
        )
        tips = []
        if agents:
            tips.append(f"prefer agent {agents[0]['agent_id']} for cost")
        busy = [a for a in agents if int(a.get("load", 0)) > 3]
        if busy:
            tips.append(f"rebalance load from {busy[0]['name']}")
        if not tips:
            tips.append("no optimization needed")
        rid = _id("aop_opt")
        return self.store.aop_analytics.save(
            rid,
            {"analytics_id": rid, "kind": "optimization", "recommendations": tips, "at": _now()},
        )
