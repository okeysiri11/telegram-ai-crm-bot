# Experience Store — execution history across platform layers.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExperienceEntry:
    entry_id: str
    category: str  # workflow | task | decision | planning | reasoning | tool | agent
    agent_id: str | None
    outcome: str  # success | failure | partial
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


class ExperienceStore:
    """In-memory experience store for learning cycles."""

    def __init__(self) -> None:
        self._workflows_success: list[ExperienceEntry] = []
        self._workflows_failed: list[ExperienceEntry] = []
        self._decisions: list[ExperienceEntry] = []
        self._planning: list[ExperienceEntry] = []
        self._reasoning: list[ExperienceEntry] = []
        self._tools: list[ExperienceEntry] = []
        self._agents: list[ExperienceEntry] = []
        self._tasks: list[ExperienceEntry] = []

    def reset(self) -> None:
        self._workflows_success.clear()
        self._workflows_failed.clear()
        self._decisions.clear()
        self._planning.clear()
        self._reasoning.clear()
        self._tools.clear()
        self._agents.clear()
        self._tasks.clear()

    def record_workflow(self, *, success: bool, agent_id: str | None, data: dict[str, Any]) -> None:
        entry = ExperienceEntry(
            entry_id=data.get("workflow_id", ""),
            category="workflow",
            agent_id=agent_id,
            outcome="success" if success else "failure",
            data=dict(data),
            timestamp=data.get("timestamp", 0.0),
        )
        (self._workflows_success if success else self._workflows_failed).append(entry)

    def record_decision(self, agent_id: str | None, data: dict[str, Any]) -> None:
        self._decisions.append(
            ExperienceEntry(
                entry_id=data.get("decision_id", ""),
                category="decision",
                agent_id=agent_id,
                outcome="success" if data.get("success", True) else "failure",
                data=dict(data),
            )
        )

    def record_planning(self, agent_id: str | None, data: dict[str, Any]) -> None:
        self._planning.append(
            ExperienceEntry(
                entry_id=data.get("plan_id", ""),
                category="planning",
                agent_id=agent_id,
                outcome="success" if data.get("success", True) else "failure",
                data=dict(data),
            )
        )

    def record_reasoning(self, agent_id: str | None, data: dict[str, Any]) -> None:
        self._reasoning.append(
            ExperienceEntry(
                entry_id=data.get("session_id", ""),
                category="reasoning",
                agent_id=agent_id,
                outcome="success" if data.get("success", True) else "failure",
                data=dict(data),
            )
        )

    def record_tool(self, agent_id: str | None, data: dict[str, Any]) -> None:
        self._tools.append(
            ExperienceEntry(
                entry_id=data.get("tool_id", ""),
                category="tool",
                agent_id=agent_id,
                outcome="success" if data.get("success", True) else "failure",
                data=dict(data),
            )
        )

    def record_agent_performance(self, agent_id: str, data: dict[str, Any]) -> None:
        self._agents.append(
            ExperienceEntry(
                entry_id=agent_id,
                category="agent",
                agent_id=agent_id,
                outcome=data.get("outcome", "success"),
                data=dict(data),
            )
        )

    def record_task(self, agent_id: str | None, data: dict[str, Any]) -> None:
        self._tasks.append(
            ExperienceEntry(
                entry_id=data.get("task_id", ""),
                category="task",
                agent_id=agent_id,
                outcome="success" if data.get("success", True) else "failure",
                data=dict(data),
            )
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "workflows_success": [e.data for e in self._workflows_success],
            "workflows_failed": [e.data for e in self._workflows_failed],
            "decisions": [e.data for e in self._decisions],
            "planning": [e.data for e in self._planning],
            "reasoning": [e.data for e in self._reasoning],
            "tools": [e.data for e in self._tools],
            "agents": [e.data for e in self._agents],
            "tasks": [e.data for e in self._tasks],
        }

    def all_entries(self) -> list[ExperienceEntry]:
        return (
            self._workflows_success
            + self._workflows_failed
            + self._decisions
            + self._planning
            + self._reasoning
            + self._tools
            + self._agents
            + self._tasks
        )

    def count(self) -> int:
        return len(self.all_entries())


experience_store = ExperienceStore()
