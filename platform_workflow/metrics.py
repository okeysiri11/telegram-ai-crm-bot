# Workflow execution metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field

from platform_workflow.models import TaskResult, TaskStatus


@dataclass
class MetricEntry:
    task_id: str
    workflow_id: str
    success: bool
    execution_time_ms: float
    assignee_id: str | None = None
    timestamp: float = field(default_factory=time.time)


class WorkflowMetrics:
    def __init__(self) -> None:
        self._entries: list[MetricEntry] = []
        self._agent_tasks: dict[str, int] = {}
        self._queue_peak: int = 0

    def reset(self) -> None:
        self._entries.clear()
        self._agent_tasks.clear()
        self._queue_peak = 0

    def record(self, result: TaskResult) -> None:
        self._entries.append(
            MetricEntry(
                task_id=result.task_id,
                workflow_id=result.workflow_id,
                success=result.success,
                execution_time_ms=result.execution_time_ms,
                assignee_id=result.assignee_id,
            )
        )
        if result.assignee_id:
            self._agent_tasks[result.assignee_id] = self._agent_tasks.get(result.assignee_id, 0) + 1

    def set_queue_length(self, length: int) -> None:
        self._queue_peak = max(self._queue_peak, length)

    def summary(self) -> dict:
        total = len(self._entries)
        if total == 0:
            return {
                "executions": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "avg_completion_time_ms": 0.0,
                "queue_peak": self._queue_peak,
                "agent_utilization": {},
            }
        successes = sum(1 for e in self._entries if e.success)
        return {
            "executions": total,
            "success_rate": round(successes / total, 4),
            "failure_rate": round((total - successes) / total, 4),
            "avg_completion_time_ms": round(sum(e.execution_time_ms for e in self._entries) / total, 2),
            "queue_peak": self._queue_peak,
            "agent_utilization": dict(self._agent_tasks),
        }


workflow_metrics = WorkflowMetrics()
