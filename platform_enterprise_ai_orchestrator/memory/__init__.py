"""AI Memory — Sprint 24.0."""

from __future__ import annotations

from typing import Any


class AIMemory:
    def __init__(self) -> None:
        self._by_agent: dict[str, dict[str, Any]] = {}

    def remember(
        self,
        *,
        agent_id: str,
        consultation: str | None = None,
        decision_id: str | None = None,
        outcome: str | None = None,
        practice: str | None = None,
        error: str | None = None,
        lesson: str | None = None,
    ) -> dict[str, Any]:
        if not agent_id:
            raise ValueError("agent_id is required")
        mem = self._by_agent.setdefault(
            agent_id,
            {
                "agent_id": agent_id,
                "consultations": [],
                "decisions": [],
                "outcomes": [],
                "successful_practices": [],
                "errors": [],
                "lessons": [],
            },
        )
        if consultation:
            mem["consultations"].append(consultation)
        if decision_id:
            mem["decisions"].append(decision_id)
        if outcome:
            mem["outcomes"].append(outcome)
        if practice:
            mem["successful_practices"].append(practice)
        if error:
            mem["errors"].append(error)
        if lesson:
            mem["lessons"].append(lesson)
        return dict(mem)

    def recall(self, agent_id: str) -> dict[str, Any]:
        return dict(self._by_agent.get(agent_id) or {"agent_id": agent_id, "empty": True})
