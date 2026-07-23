"""Result aggregator — merge agent outputs, resolve conflicts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ResultAggregator:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def aggregate(self, *, execution_id: str) -> dict[str, Any]:
        exe = self.store.aop_executions.get(execution_id)
        if not exe:
            raise NotFoundError(f"execution not found: {execution_id}")
        steps = [s for s in (exe.get("step_results") or []) if s.get("status") == "ok"]
        ranked = sorted(steps, key=lambda s: s.get("cost", 0))
        total_cost = sum(float(s.get("cost", 0) or 0) for s in steps)
        contradictions = []
        summaries = [s.get("summary", "") for s in steps]
        if len(set(summaries)) != len(summaries):
            contradictions.append("duplicate summaries detected")
        aid = _id("aop_agg")
        return self.store.aop_aggregations.save(
            aid,
            {
                "aggregation_id": aid,
                "execution_id": execution_id,
                "task_id": exe.get("task_id"),
                "ranked": ranked,
                "merged_summary": " | ".join(summaries),
                "total_cost": total_cost,
                "contradictions": contradictions,
                "result": {
                    "ok": exe.get("status") == "completed",
                    "steps": len(steps),
                    "output": summaries,
                },
                "at": _now(),
            },
        )
