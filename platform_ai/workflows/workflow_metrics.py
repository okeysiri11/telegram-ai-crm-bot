# Workflow execution metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from platform_ai.workflows.models import WorkflowExecutionResult


@dataclass
class WorkflowMetricEntry:
    workflow_id: str
    success: bool
    latency_ms: float
    cost_usd: float = 0.0
    steps: int = 0
    timestamp: float = field(default_factory=time.time)


class WorkflowMetrics:
    def __init__(self) -> None:
        self._entries: list[WorkflowMetricEntry] = []

    def reset(self) -> None:
        self._entries.clear()

    def record(self, result: WorkflowExecutionResult) -> None:
        self._entries.append(
            WorkflowMetricEntry(
                workflow_id=result.workflow_id,
                success=result.status == "completed",
                latency_ms=result.latency_ms,
                cost_usd=result.cost_usd,
                steps=len(result.step_results),
            )
        )

    def for_workflow(self, workflow_id: str) -> dict[str, Any]:
        entries = [e for e in self._entries if e.workflow_id == workflow_id]
        if not entries:
            return {
                "workflow_id": workflow_id,
                "executions": 0,
                "success_rate": 0.0,
                "failures": 0,
                "avg_latency_ms": 0.0,
                "avg_cost_usd": 0.0,
                "avg_steps": 0.0,
            }
        successes = sum(1 for e in entries if e.success)
        return {
            "workflow_id": workflow_id,
            "executions": len(entries),
            "success_rate": round(successes / len(entries), 4),
            "failures": len(entries) - successes,
            "avg_latency_ms": round(sum(e.latency_ms for e in entries) / len(entries), 2),
            "avg_cost_usd": round(sum(e.cost_usd for e in entries) / len(entries), 6),
            "avg_steps": round(sum(e.steps for e in entries) / len(entries), 1),
        }

    def summary(self) -> dict[str, Any]:
        ids = {e.workflow_id for e in self._entries}
        running = sum(1 for e in self._entries if e.timestamp > time.time() - 60)
        return {
            "total_executions": len(self._entries),
            "workflows": {wid: self.for_workflow(wid) for wid in sorted(ids)},
            "recent_executions": running,
        }


workflow_metrics = WorkflowMetrics()
