# Orchestrator metrics — execution time, failures, retries, routing.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from platform_orchestrator.models import RoutingDecision, TaskResult, TaskStatus


@dataclass
class ExecutionMetric:
    task_id: str
    agent_id: str
    capability: str
    status: str
    execution_time_ms: float
    retries: int
    timestamp: float = field(default_factory=time.time)


class OrchestratorMetrics:
    def __init__(self) -> None:
        self._executions: list[ExecutionMetric] = []
        self._routing_decisions: list[dict[str, Any]] = []
        self._failures: int = 0
        self._retries: int = 0
        self._active_agents: set[str] = set()
        self._queue_length: int = 0

    def reset(self) -> None:
        self._executions.clear()
        self._routing_decisions.clear()
        self._failures = 0
        self._retries = 0
        self._active_agents.clear()
        self._queue_length = 0

    def record_routing(self, decision: RoutingDecision) -> None:
        self._routing_decisions.append(
            {
                "capability": decision.capability,
                "agent_id": decision.agent_id,
                "reason": decision.reason,
                "priority": decision.priority,
                "timestamp": time.time(),
            }
        )

    def record_execution(self, result: TaskResult) -> None:
        self._executions.append(
            ExecutionMetric(
                task_id=result.task_id,
                agent_id=result.agent_id,
                capability=result.capability,
                status=result.status.value,
                execution_time_ms=result.execution_time_ms,
                retries=result.retries,
            )
        )
        if result.status != TaskStatus.COMPLETED:
            self._failures += 1
        self._retries += result.retries

    def set_active_agents(self, agent_ids: set[str]) -> None:
        self._active_agents = set(agent_ids)

    def set_queue_length(self, length: int) -> None:
        self._queue_length = length

    def summary(self) -> dict[str, Any]:
        total = len(self._executions)
        if total == 0:
            avg_ms = 0.0
            success_rate = 0.0
        else:
            avg_ms = round(sum(e.execution_time_ms for e in self._executions) / total, 2)
            successes = sum(1 for e in self._executions if e.status == TaskStatus.COMPLETED.value)
            success_rate = round(successes / total, 4)

        return {
            "executions": total,
            "failures": self._failures,
            "retries": self._retries,
            "avg_execution_time_ms": avg_ms,
            "success_rate": success_rate,
            "routing_decisions": len(self._routing_decisions),
            "active_agents": len(self._active_agents),
            "queue_length": self._queue_length,
            "recent_routing": self._routing_decisions[-10:],
        }

    def for_agent(self, agent_id: str) -> dict[str, Any]:
        entries = [e for e in self._executions if e.agent_id == agent_id]
        if not entries:
            return {"agent_id": agent_id, "executions": 0, "failures": 0, "avg_execution_time_ms": 0.0}
        failures = sum(1 for e in entries if e.status != TaskStatus.COMPLETED.value)
        return {
            "agent_id": agent_id,
            "executions": len(entries),
            "failures": failures,
            "avg_execution_time_ms": round(sum(e.execution_time_ms for e in entries) / len(entries), 2),
        }


orchestrator_metrics = OrchestratorMetrics()
