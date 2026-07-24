"""Cost Optimization — Sprint 24.9."""

from __future__ import annotations

from typing import Any


class CostOptimization:
    def track(
        self,
        *,
        entries: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        entries = list(entries or [])
        by_provider: dict[str, float] = {}
        by_client: dict[str, float] = {}
        by_agent: dict[str, float] = {}
        by_unit: dict[str, float] = {}
        by_task: dict[str, float] = {}
        total = 0.0
        for e in entries:
            cost = float(e.get("cost", 0))
            total += cost
            by_provider[e.get("provider_id", "unknown")] = by_provider.get(e.get("provider_id", "unknown"), 0) + cost
            by_client[e.get("client_id", "unknown")] = by_client.get(e.get("client_id", "unknown"), 0) + cost
            by_agent[e.get("agent_id", "unknown")] = by_agent.get(e.get("agent_id", "unknown"), 0) + cost
            by_unit[e.get("unit", "unknown")] = by_unit.get(e.get("unit", "unknown"), 0) + cost
            by_task[e.get("task_type", "unknown")] = by_task.get(e.get("task_type", "unknown"), 0) + cost
        return {
            "total_cost": round(total, 6),
            "by_provider": by_provider,
            "by_client": by_client,
            "by_agent": by_agent,
            "by_unit": by_unit,
            "by_task": by_task,
            "entry_count": len(entries),
        }
