# Executive AI layer — C-suite autonomous agents.

from __future__ import annotations

from events.publisher import publish

from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store
from ecosystem.workforce.events import ExecutiveDecisionMadeEvent
from ecosystem.workforce.models import ExecutiveAgent, ExecutiveDecision, ExecutiveRole, TaskStatus, WorkforceTask


EXECUTIVE_DEFS: list[tuple[ExecutiveRole, str, int, list[str]]] = [
    (ExecutiveRole.CEO, "Chief Executive AI", 100, ["*"]),
    (ExecutiveRole.COO, "Chief Operations AI", 90, ["operations", "support", "logistics"]),
    (ExecutiveRole.CFO, "Chief Financial AI", 90, ["finance"]),
    (ExecutiveRole.CSO, "Chief Sales AI", 90, ["sales"]),
    (ExecutiveRole.CMO, "Chief Marketing AI", 90, ["marketing"]),
    (ExecutiveRole.CTO, "Chief Technology AI", 90, ["development"]),
    (ExecutiveRole.CLO, "Chief Legal AI", 90, ["legal"]),
    (ExecutiveRole.CAO, "Chief Analytics AI", 85, ["operations", "finance", "sales"]),
]


class ExecutiveService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store
        self._seed()

    def _seed(self) -> None:
        if self._store.executives.count() > 0:
            return
        for role, name, authority, depts in EXECUTIVE_DEFS:
            agent = ExecutiveAgent(role=role, name=name, authority_level=authority, departments=depts)
            self._store.executives.save(agent.executive_id, agent)

    def _ensure_seeded(self) -> None:
        if self._store.executives.count() == 0:
            self._seed()

    def list_executives(self) -> list[ExecutiveAgent]:
        self._ensure_seeded()
        return sorted(self._store.executives.list_all(), key=lambda e: -e.authority_level)

    def get_by_role(self, role: ExecutiveRole) -> ExecutiveAgent:
        self._ensure_seeded()
        for executive in self._store.executives.list_all():
            if executive.role == role:
                return executive
        raise NotFoundError("Executive", role.value)

    async def decide(
        self,
        role: ExecutiveRole,
        title: str,
        *,
        rationale: str = "",
        approved: bool = True,
        task_id: str = "",
        metadata: dict | None = None,
    ) -> ExecutiveDecision:
        self.get_by_role(role)
        decision = ExecutiveDecision(
            executive_role=role,
            title=title,
            rationale=rationale or f"{role.value} decision on {title}",
            approved=approved,
            task_id=task_id,
            metadata=metadata or {},
        )
        self._store.executive_decisions.save(decision.decision_id, decision)
        await publish(
            ExecutiveDecisionMadeEvent(
                decision_id=decision.decision_id,
                executive_role=role.value,
                title=title,
                approved=approved,
                task_id=task_id,
            )
        )
        return decision

    async def approve_task(self, role: ExecutiveRole, task: WorkforceTask, *, rationale: str = "") -> ExecutiveDecision:
        if not task.requires_approval and task.status.value != "awaiting_approval":
            raise ValidationError("Task does not require approval")
        decision = await self.decide(
            role,
            f"Approve: {task.title}",
            rationale=rationale or "Executive approval granted",
            approved=True,
            task_id=task.task_id,
        )
        task.approved_by = role.value
        task.status = TaskStatus.ASSIGNED
        self._store.workforce_tasks.save(task.task_id, task)
        return decision

    def decision_support(self, topic: str, *, context: dict | None = None) -> dict:
        self._ensure_seeded()
        return {
            "topic": topic,
            "context": context or {},
            "recommendation": f"Prioritize {topic} with cross-department alignment",
            "suggested_owner": ExecutiveRole.CEO.value,
            "risk_level": "medium" if not context else "low",
            "next_steps": ["Gather department input", "Draft decision", "Execute"],
        }

    def list_decisions(self, *, role: ExecutiveRole | None = None) -> list[ExecutiveDecision]:
        decisions = self._store.executive_decisions.list_all()
        if role:
            decisions = [d for d in decisions if d.executive_role == role]
        return sorted(decisions, key=lambda d: d.created_at, reverse=True)


executive_service = ExecutiveService()
