# Workforce engine — autonomous AI workforce facade.

from __future__ import annotations

from typing import Any

from ecosystem.config import DEFAULT_CONFIG
from ecosystem.workforce.coordination.service import CoordinationService, coordination_service
from ecosystem.workforce.departments.service import DepartmentService, department_service
from ecosystem.workforce.execution.service import ExecutionService, execution_service
from ecosystem.workforce.executive.service import ExecutiveService, executive_service
from ecosystem.workforce.governance.service import GovernanceService, governance_service
from ecosystem.workforce.management.service import ManagementService, management_service
from ecosystem.workforce.planning.service import PlanningService, planning_service
from ecosystem.workforce.specialists.service import SpecialistService, specialist_service


class WorkforceEngine:
    """Autonomous AI workforce — executives, departments, specialists, planning."""

    def __init__(
        self,
        executives: ExecutiveService | None = None,
        departments: DepartmentService | None = None,
        specialists: SpecialistService | None = None,
        coordination: CoordinationService | None = None,
        planning: PlanningService | None = None,
        governance: GovernanceService | None = None,
        management: ManagementService | None = None,
        execution: ExecutionService | None = None,
    ) -> None:
        self.executives = executives or executive_service
        self.departments = departments or department_service
        self.specialists = specialists or specialist_service
        self.coordination = coordination or coordination_service
        self.planning = planning or planning_service
        self.governance = governance or governance_service
        self.management = management or management_service
        self.execution = execution or execution_service

    def metrics(self) -> dict[str, Any]:
        from ecosystem.shared.store import ecosystem_store

        return {
            "ecosystem_version": DEFAULT_CONFIG.ecosystem_version,
            "workforce_layer": DEFAULT_CONFIG.workforce_layer,
            "executive_ai": DEFAULT_CONFIG.executive_ai,
            "executives": ecosystem_store.executives.count(),
            "departments": ecosystem_store.workforce_departments.count(),
            "specialists": ecosystem_store.specialists.count(),
            "tasks": ecosystem_store.workforce_tasks.count(),
            "objectives": ecosystem_store.objectives.count(),
            "plans": ecosystem_store.work_plans.count(),
            "escalations": ecosystem_store.escalations.count(),
            "collaborations": ecosystem_store.collaboration_sessions.count(),
        }


workforce_engine = WorkforceEngine()
