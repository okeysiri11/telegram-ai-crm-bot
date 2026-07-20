# Planning engine metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field

from platform_planning.models import PlanningResult


@dataclass
class PlanningMetricEntry:
    plan_id: str
    strategy: str
    step_count: int
    success: bool
    planning_time_ms: float
    replan_count: int = 0
    timestamp: float = field(default_factory=time.time)


class PlanningMetrics:
    def __init__(self) -> None:
        self._entries: list[PlanningMetricEntry] = []

    def reset(self) -> None:
        self._entries.clear()

    def record(self, result: PlanningResult, *, replan_count: int = 0) -> None:
        self._entries.append(
            PlanningMetricEntry(
                plan_id=result.plan.plan_id,
                strategy=result.plan.strategy.value,
                step_count=result.plan.step_count,
                success=result.success,
                planning_time_ms=result.planning_time_ms,
                replan_count=replan_count,
            )
        )

    def summary(self) -> dict:
        total = len(self._entries)
        if total == 0:
            return {
                "plans": 0,
                "avg_planning_latency_ms": 0.0,
                "avg_plan_size": 0.0,
                "plan_success_rate": 0.0,
                "replanning_count": 0,
                "execution_efficiency": 0.0,
            }
        successes = sum(1 for e in self._entries if e.success)
        return {
            "plans": total,
            "avg_planning_latency_ms": round(sum(e.planning_time_ms for e in self._entries) / total, 2),
            "avg_plan_size": round(sum(e.step_count for e in self._entries) / total, 1),
            "plan_success_rate": round(successes / total, 4),
            "replanning_count": sum(e.replan_count for e in self._entries),
            "execution_efficiency": round(successes / total * (1 - sum(e.replan_count for e in self._entries) / max(total, 1) * 0.1), 4),
        }


planning_metrics = PlanningMetrics()
