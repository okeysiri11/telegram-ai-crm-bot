"""Performance analytics per agent."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PerformanceAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self, *, agent_id: str | None = None) -> dict[str, Any]:
        executions = self.store.aop_executions.list_all()
        by_agent: dict[str, dict[str, Any]] = {}
        for exe in executions:
            for step in exe.get("step_results") or []:
                aid = step.get("agent_id")
                if not aid:
                    continue
                if agent_id and aid != agent_id:
                    continue
                bucket = by_agent.setdefault(
                    aid,
                    {"tasks": 0, "ok": 0, "duration_ms": 0.0, "cost": 0.0},
                )
                bucket["tasks"] += 1
                if step.get("status") == "ok":
                    bucket["ok"] += 1
                bucket["duration_ms"] += float(step.get("duration_ms", 0) or 0)
                bucket["cost"] += float(step.get("cost", 0) or 0)

        agents = []
        for aid, b in by_agent.items():
            tasks = b["tasks"] or 1
            agents.append(
                {
                    "agent_id": aid,
                    "tasks": b["tasks"],
                    "avg_duration_ms": b["duration_ms"] / tasks,
                    "success_rate": b["ok"] / tasks,
                    "load": next(
                        (a.get("load", 0) for a in self.store.aop_agents.list_all() if a.get("agent_id") == aid),
                        0,
                    ),
                    "quality": b["ok"] / tasks,
                }
            )
        rid = _id("aop_perf")
        return self.store.aop_analytics.save(
            rid,
            {"analytics_id": rid, "kind": "performance", "agents": agents, "at": _now()},
        )
