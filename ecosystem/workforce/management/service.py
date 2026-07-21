# Management layer — department managers bridging executives and specialists.

from __future__ import annotations

from typing import Any

from ecosystem.workforce.departments.service import DepartmentService, department_service
from ecosystem.workforce.models import DepartmentType
from ecosystem.workforce.specialists.service import SpecialistService, specialist_service


class ManagementService:
    def __init__(
        self,
        departments: DepartmentService | None = None,
        specialists: SpecialistService | None = None,
    ) -> None:
        self.departments = departments or department_service
        self.specialists = specialists or specialist_service

    def department_roster(self, department_type: DepartmentType) -> dict[str, Any]:
        dept = self.departments.get_by_type(department_type)
        specialists = self.specialists.list_specialists(department_type=department_type)
        return {
            "department": dept.to_dict(),
            "specialists": [s.to_dict() for s in specialists],
            "available_capacity": max(0, dept.capacity - dept.workload),
        }

    def org_chart(self) -> dict[str, Any]:
        chart = []
        for dept in self.departments.list_departments():
            chart.append(
                {
                    "department": dept.to_dict(),
                    "specialists": [
                        s.to_dict()
                        for s in self.specialists.list_specialists(department_type=dept.department_type)
                    ],
                }
            )
        return {"departments": chart}


management_service = ManagementService()
