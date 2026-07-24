"""AI Registry — Sprint 24.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_ai_orchestrator.models import COUNCIL_ROLES, DEFAULT_COMPETENCIES


class AIRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, dict[str, Any]] = {}

    def register(
        self,
        *,
        agent_id: str,
        role: str,
        competencies: list[str] | None = None,
        access_level: str = "council",
        status: str = "active",
    ) -> dict[str, Any]:
        if not agent_id:
            raise ValueError("agent_id is required")
        role = (role or "").lower()
        agent = {
            "agent_id": agent_id,
            "role": role,
            "competencies": list(competencies or DEFAULT_COMPETENCIES.get(role, [role])),
            "access_level": access_level,
            "decision_history": [],
            "effectiveness": {"decisions": 0, "approved": 0, "score": 1.0},
            "status": status or "active",
        }
        self._agents[agent_id] = agent
        return dict(agent)

    def seed_council(self) -> list[dict[str, Any]]:
        seeded = []
        for role in COUNCIL_ROLES:
            seeded.append(self.register(agent_id=f"ai_{role}", role=role))
        return seeded

    def get(self, agent_id: str) -> dict[str, Any] | None:
        a = self._agents.get(agent_id)
        return dict(a) if a else None

    def list_agents(self, *, status: str | None = None) -> list[dict[str, Any]]:
        agents = [dict(a) for a in self._agents.values()]
        if status:
            agents = [a for a in agents if a.get("status") == status]
        return agents

    def record_decision(self, agent_id: str, decision_id: str) -> dict[str, Any]:
        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError(f"unknown agent: {agent_id}")
        hist = list(agent.get("decision_history") or [])
        hist.append(decision_id)
        agent["decision_history"] = hist[-50:]
        eff = dict(agent.get("effectiveness") or {})
        eff["decisions"] = int(eff.get("decisions", 0)) + 1
        agent["effectiveness"] = eff
        return dict(agent)

    def add_agent(self, **kwargs: Any) -> dict[str, Any]:
        """Extensibility: register agents without changing orchestrator core."""
        return self.register(**kwargs)
