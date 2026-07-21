# Governance — escalation policies, approval rules, audit.

from __future__ import annotations

from typing import Any

from ecosystem.shared.store import EcosystemStore, ecosystem_store
from ecosystem.workforce.models import ExecutiveRole, TaskPriority, WorkforceTask


class GovernanceService:
    """Workforce governance policies and compliance checks."""

    APPROVAL_REQUIRED_PRIORITIES = {TaskPriority.CRITICAL, TaskPriority.HIGH}

    ESCALATION_RULES = [
        {"from": "specialist", "to": ExecutiveRole.COO.value, "when": "blocked_over_24h"},
        {"from": "department", "to": ExecutiveRole.CEO.value, "when": "cross_department_conflict"},
        {"from": "any", "to": ExecutiveRole.CEO.value, "when": "critical_priority"},
    ]

    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def requires_executive_approval(self, task: WorkforceTask) -> bool:
        return task.requires_approval or task.priority in self.APPROVAL_REQUIRED_PRIORITIES

    def escalation_policy(self) -> list[dict[str, str]]:
        return [dict(r) for r in self.ESCALATION_RULES]

    def audit_trail(self) -> dict[str, Any]:
        return {
            "decisions": self._store.executive_decisions.count(),
            "escalations": self._store.escalations.count(),
            "completed_tasks": len(
                [t for t in self._store.workforce_tasks.list_all() if t.status.value == "completed"]
            ),
            "open_escalations": [
                e.to_dict() for e in self._store.escalations.list_all() if not e.resolved
            ],
        }

    def compliance_check(self) -> dict[str, Any]:
        tasks = self._store.workforce_tasks.list_all()
        unapproved_critical = [
            t.task_id
            for t in tasks
            if t.priority in self.APPROVAL_REQUIRED_PRIORITIES
            and t.status.value == "in_progress"
            and not t.approved_by
        ]
        return {
            "compliant": len(unapproved_critical) == 0,
            "unapproved_critical_tasks": unapproved_critical,
            "policy_version": "1.0",
        }


governance_service = GovernanceService()
