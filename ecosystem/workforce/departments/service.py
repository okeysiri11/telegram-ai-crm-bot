# Department layer — sales, finance, marketing, ops, support, dev, legal, logistics.

from __future__ import annotations

from ecosystem.shared.exceptions import NotFoundError
from ecosystem.shared.store import EcosystemStore, ecosystem_store
from ecosystem.workforce.models import DEPARTMENT_EXECUTIVE, Department, DepartmentType


class DepartmentService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store
        self._seed()

    def _seed(self) -> None:
        if self._store.workforce_departments.count() > 0:
            return
        for dept_type in DepartmentType:
            dept = Department(
                department_type=dept_type,
                name=f"{dept_type.value.replace('_', ' ').title()} Department",
                executive_role=DEPARTMENT_EXECUTIVE[dept_type],
                capacity=100,
            )
            self._store.workforce_departments.save(dept.department_id, dept)

    def _ensure_seeded(self) -> None:
        if self._store.workforce_departments.count() == 0:
            self._seed()

    def list_departments(self) -> list[Department]:
        self._ensure_seeded()
        return self._store.workforce_departments.list_all()

    def get_by_type(self, department_type: DepartmentType) -> Department:
        self._ensure_seeded()
        for dept in self._store.workforce_departments.list_all():
            if dept.department_type == department_type:
                return dept
        raise NotFoundError("Department", department_type.value)

    def adjust_workload(self, department_type: DepartmentType, delta: int) -> Department:
        dept = self.get_by_type(department_type)
        dept.workload = max(0, dept.workload + delta)
        self._store.workforce_departments.save(dept.department_id, dept)
        return dept

    def least_loaded(self, candidates: list[DepartmentType] | None = None) -> Department:
        depts = self.list_departments()
        if candidates:
            depts = [d for d in depts if d.department_type in candidates]
        return min(depts, key=lambda d: d.workload / d.capacity if d.capacity else 1)


department_service = DepartmentService()
