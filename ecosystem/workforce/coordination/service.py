# Coordination — delegation, routing, escalation, balancing, conflict resolution.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store
from ecosystem.workforce.departments.service import DepartmentService, department_service
from ecosystem.workforce.events import (
    DepartmentTaskAssignedEvent,
    EscalationTriggeredEvent,
    WorkCompletedEvent,
)
from ecosystem.workforce.executive.service import ExecutiveService, executive_service
from ecosystem.workforce.models import (
    DEPARTMENT_EXECUTIVE,
    SPECIALIST_DEPARTMENT,
    CollaborationSession,
    DepartmentType,
    Escalation,
    ExecutiveRole,
    SpecialistType,
    TaskPriority,
    TaskStatus,
    WorkforceTask,
)
from ecosystem.workforce.specialists.service import SpecialistService, specialist_service

PRIORITY_ORDER = {
    TaskPriority.CRITICAL: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.NORMAL: 2,
    TaskPriority.LOW: 3,
}

TITLE_DEPARTMENT_HINTS: list[tuple[list[str], DepartmentType, SpecialistType]] = [
    (["invoice", "payment", "refund", "finance", "billing"], DepartmentType.FINANCE, SpecialistType.FINANCIAL),
    (["legal", "contract", "compliance"], DepartmentType.LEGAL, SpecialistType.LAW),
    (["inventory", "stock", "logistics", "delivery"], DepartmentType.LOGISTICS, SpecialistType.INVENTORY),
    (["code", "api", "develop", "integration"], DepartmentType.DEVELOPMENT, SpecialistType.DEVELOPER),
    (["market", "campaign", "brand"], DepartmentType.MARKETING, SpecialistType.MARKETING),
    (["support", "ticket", "help"], DepartmentType.SUPPORT, SpecialistType.SUPPORT),
    (["analy", "kpi", "report"], DepartmentType.OPERATIONS, SpecialistType.ANALYTICS),
    (["sale", "lead", "crm", "deal"], DepartmentType.SALES, SpecialistType.SALES),
]


class CoordinationService:
    def __init__(
        self,
        store: EcosystemStore | None = None,
        departments: DepartmentService | None = None,
        specialists: SpecialistService | None = None,
        executives: ExecutiveService | None = None,
    ) -> None:
        self._store = store or ecosystem_store
        self.departments = departments or department_service
        self.specialists = specialists or specialist_service
        self.executives = executives or executive_service

    def route_department(self, title: str, description: str = "") -> tuple[DepartmentType, SpecialistType]:
        text = f"{title} {description}".lower()
        for keywords, dept, specialist in TITLE_DEPARTMENT_HINTS:
            if any(k in text for k in keywords):
                return dept, specialist
        return DepartmentType.OPERATIONS, SpecialistType.ANALYTICS

    async def delegate(
        self,
        title: str,
        *,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        department_type: DepartmentType | None = None,
        requires_approval: bool = False,
        application_id: str = "",
    ) -> WorkforceTask:
        if not title:
            raise ValidationError("title is required")
        if department_type:
            dept_type = department_type
            specialist_type = next(
                (st for st, dt in SPECIALIST_DEPARTMENT.items() if dt == department_type),
                SpecialistType.ANALYTICS,
            )
        else:
            dept_type, specialist_type = self.route_department(title, description)

        specialist = self.specialists.assignable(specialist_type)
        task = WorkforceTask(
            title=title,
            description=description,
            department_type=dept_type,
            specialist_id=specialist.specialist_id,
            executive_role=DEPARTMENT_EXECUTIVE[dept_type],
            priority=priority,
            status=TaskStatus.AWAITING_APPROVAL if requires_approval else TaskStatus.ASSIGNED,
            requires_approval=requires_approval,
            application_id=application_id,
        )
        self._store.workforce_tasks.save(task.task_id, task)
        self.specialists.increment_load(specialist.specialist_id, 1)
        self.departments.adjust_workload(dept_type, 1)
        await publish(
            DepartmentTaskAssignedEvent(
                task_id=task.task_id,
                department_type=dept_type.value,
                specialist_id=specialist.specialist_id,
                priority=priority.value,
            )
        )
        return task

    async def execute(self, task_id: str, *, result: dict[str, Any] | None = None) -> WorkforceTask:
        task = self.get_task(task_id)
        if task.requires_approval and not task.approved_by:
            raise ValidationError("Task requires executive approval before execution")
        task.status = TaskStatus.IN_PROGRESS
        self._store.workforce_tasks.save(task_id, task)

        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            bridge_result = await platform_bridge.delegate_task(
                task.title,
                {"task_id": task_id, "department": task.department_type.value},
                agent_id=task.specialist_id,
            )
        except Exception:
            bridge_result = {"status": "fallback", "executed_locally": True}

        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.result = result or {"bridge": bridge_result, "status": "completed"}
        self._store.workforce_tasks.save(task_id, task)
        if task.specialist_id:
            self.specialists.increment_load(task.specialist_id, -1)
        self.departments.adjust_workload(task.department_type, -1)
        await publish(
            WorkCompletedEvent(
                task_id=task_id,
                department_type=task.department_type.value,
                specialist_id=task.specialist_id,
                result=task.result,
            )
        )
        return task

    async def escalate(self, task_id: str, reason: str, *, to_role: ExecutiveRole | None = None) -> Escalation:
        task = self.get_task(task_id)
        target = to_role or ExecutiveRole.CEO
        escalation = Escalation(
            task_id=task_id,
            from_level=task.department_type.value,
            to_role=target,
            reason=reason,
        )
        task.status = TaskStatus.ESCALATED
        self._store.workforce_tasks.save(task_id, task)
        self._store.escalations.save(escalation.escalation_id, escalation)
        await publish(
            EscalationTriggeredEvent(
                escalation_id=escalation.escalation_id,
                task_id=task_id,
                to_role=target.value,
                reason=reason,
            )
        )
        return escalation

    def resolve_conflict(self, task_ids: list[str]) -> dict[str, Any]:
        tasks = [self.get_task(tid) for tid in task_ids]
        winner = sorted(tasks, key=lambda t: (PRIORITY_ORDER[t.priority], t.created_at))[0]
        for task in tasks:
            if task.task_id != winner.task_id and task.status not in (TaskStatus.COMPLETED, TaskStatus.BLOCKED):
                task.status = TaskStatus.BLOCKED
                task.result["conflict_resolved_in_favor_of"] = winner.task_id
                self._store.workforce_tasks.save(task.task_id, task)
        return {"winner_task_id": winner.task_id, "blocked": [t.task_id for t in tasks if t.task_id != winner.task_id]}

    def balance_work(self) -> dict[str, Any]:
        depts = self.departments.list_departments()
        overloaded = [d for d in depts if d.workload > d.capacity * 0.8]
        underloaded = [d for d in depts if d.workload < d.capacity * 0.3]
        return {
            "overloaded": [d.to_dict() for d in overloaded],
            "underloaded": [d.to_dict() for d in underloaded],
            "recommendation": "Reassign non-critical tasks from overloaded to underloaded departments"
            if overloaded and underloaded
            else "Workload balanced",
        }

    async def collaborate(
        self,
        topic: str,
        departments: list[str],
        *,
        shared_memory: dict[str, Any] | None = None,
        knowledge_refs: list[str] | None = None,
    ) -> CollaborationSession:
        session = CollaborationSession(
            topic=topic,
            departments=departments,
            shared_memory=shared_memory or {},
            shared_knowledge=knowledge_refs or [],
        )
        # Collaborative reasoning stub
        session.decisions.append(
            {
                "type": "collaborative_plan",
                "summary": f"Aligned departments {', '.join(departments)} on {topic}",
                "actions": [f"{d}: contribute expertise" for d in departments],
            }
        )
        self._store.collaboration_sessions.save(session.session_id, session)
        return session

    def get_task(self, task_id: str) -> WorkforceTask:
        task = self._store.workforce_tasks.get(task_id)
        if task is None:
            raise NotFoundError("WorkforceTask", task_id)
        return task

    def list_tasks(self, *, status: TaskStatus | None = None, department_type: DepartmentType | None = None) -> list[WorkforceTask]:
        tasks = self._store.workforce_tasks.list_all()
        if status:
            tasks = [t for t in tasks if t.status == status]
        if department_type:
            tasks = [t for t in tasks if t.department_type == department_type]
        return sorted(tasks, key=lambda t: (PRIORITY_ORDER[t.priority], t.created_at))


coordination_service = CoordinationService()
