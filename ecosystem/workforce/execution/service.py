# Execution facade — run delegated tasks end-to-end.

from __future__ import annotations

from typing import Any

from ecosystem.workforce.coordination.service import CoordinationService, coordination_service
from ecosystem.workforce.executive.service import ExecutiveService, executive_service
from ecosystem.workforce.governance.service import GovernanceService, governance_service
from ecosystem.workforce.models import DepartmentType, ExecutiveRole, TaskPriority, WorkforceTask


class ExecutionService:
    def __init__(
        self,
        coordination: CoordinationService | None = None,
        executives: ExecutiveService | None = None,
        governance: GovernanceService | None = None,
    ) -> None:
        self.coordination = coordination or coordination_service
        self.executives = executives or executive_service
        self.governance = governance or governance_service

    async def run(
        self,
        title: str,
        *,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        department_type: DepartmentType | None = None,
        application_id: str = "",
        auto_approve: bool = True,
    ) -> WorkforceTask:
        requires_approval = priority in self.governance.APPROVAL_REQUIRED_PRIORITIES
        task = await self.coordination.delegate(
            title,
            description=description,
            priority=priority,
            department_type=department_type,
            requires_approval=requires_approval,
            application_id=application_id,
        )
        if requires_approval and auto_approve:
            role = task.executive_role or ExecutiveRole.CEO
            await self.executives.approve_task(role, task)
        return await self.coordination.execute(task.task_id)

    async def run_batch(self, jobs: list[dict[str, Any]]) -> list[WorkforceTask]:
        results = []
        for job in jobs:
            priority = TaskPriority(job.get("priority", "normal"))
            dept = DepartmentType(job["department_type"]) if job.get("department_type") else None
            results.append(
                await self.run(
                    job["title"],
                    description=job.get("description", ""),
                    priority=priority,
                    department_type=dept,
                    application_id=job.get("application_id", ""),
                )
            )
        return results


execution_service = ExecutionService()
