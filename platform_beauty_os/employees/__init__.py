"""Employee management — Sprint 22.2."""

from __future__ import annotations

from typing import Any


class EmployeeManagement:
    def create(
        self,
        *,
        name: str,
        role: str,
        specialization: str = "",
        services: list[str] | None = None,
        commission_pct: float = 0.4,
        salary: float = 0.0,
        schedule: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not name or not role:
            raise ValueError("employee name and role are required")
        return {
            "name": name.strip(),
            "role": role,
            "specialization": specialization,
            "services": list(services or []),
            "commission_pct": commission_pct,
            "salary": salary,
            "schedule": schedule or {},
            "vacation": [],
            "rating": 5.0,
            "performance": 0.0,
        }
