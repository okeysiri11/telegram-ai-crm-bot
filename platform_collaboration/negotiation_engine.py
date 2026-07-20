# NegotiationEngine — task ownership, priority, resource, tool negotiation.

from __future__ import annotations

from platform_collaboration.config import DEFAULT_COLLABORATION_CONFIG, CollaborationEngineConfig
from platform_collaboration.models import (
    AgentParticipant,
    CollaborationSession,
    CollaborationTask,
    NegotiationResult,
)


class NegotiationEngine:
    def __init__(self, *, config: CollaborationEngineConfig | None = None) -> None:
        self._config = config or DEFAULT_COLLABORATION_CONFIG

    def negotiate_task_ownership(
        self,
        session: CollaborationSession,
        task: CollaborationTask,
    ) -> NegotiationResult:
        conflicts: list[str] = []
        candidates = self._capable_agents(session, task.capability)

        if not candidates:
            if session.supervisor_id and session.supervisor_id in session.participants:
                return NegotiationResult(success=True, task_id=task.task_id, owner_id=session.supervisor_id, rounds=1)
            return NegotiationResult(success=False, task_id=task.task_id, conflicts=["no_capable_agent"])

        claims: dict[str, float] = {}
        for agent_id in candidates:
            p = session.participants[agent_id]
            score = p.confidence
            if task.capability and task.capability in p.capabilities:
                score += 20.0
            if p.status == "active":
                score += 10.0
            claims[agent_id] = score

        if len(claims) > 1:
            top_two = sorted(claims.values(), reverse=True)[:2]
            if len(top_two) == 2 and abs(top_two[0] - top_two[1]) < 5:
                conflicts.append("ownership_dispute")

        owner_id = max(claims, key=claims.get)  # type: ignore[arg-type]
        agreed_priority = self._negotiate_priority(session, task, owner_id)

        return NegotiationResult(
            success=True,
            task_id=task.task_id,
            owner_id=owner_id,
            agreed_priority=agreed_priority,
            rounds=2 if conflicts else 1,
            conflicts=conflicts,
        )

    def negotiate_tool_selection(
        self,
        session: CollaborationSession,
        task: CollaborationTask,
        available_tools: list[str],
    ) -> str | None:
        if not available_tools:
            return None
        capability = task.capability or ""
        for tool in available_tools:
            if capability.split("_")[0] in tool or capability in tool:
                return tool
        return available_tools[0]

    def negotiate_resources(
        self,
        session: CollaborationSession,
        task: CollaborationTask,
    ) -> dict[str, float]:
        active = [p for p in session.participants.values() if p.status == "active"]
        share = 100.0 / max(len(active), 1)
        return {p.agent_id: share for p in active}

    def _negotiate_priority(
        self,
        session: CollaborationSession,
        task: CollaborationTask,
        owner_id: str,
    ) -> float:
        owner = session.participants.get(owner_id)
        base = task.priority
        if owner and owner.role.value == "supervisor":
            return min(base + 10.0, 100.0)
        return base

    def _capable_agents(self, session: CollaborationSession, capability: str | None) -> list[str]:
        if not capability:
            return list(session.participants.keys())
        return [
            aid for aid, p in session.participants.items()
            if capability in p.capabilities or not p.capabilities
        ]


negotiation_engine = NegotiationEngine()
