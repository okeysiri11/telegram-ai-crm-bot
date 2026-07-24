"""Branch management — Sprint 22.2."""

from __future__ import annotations

from typing import Any


class BranchManagement:
    def create(
        self,
        *,
        name: str,
        schedule: dict[str, Any] | None = None,
        address: str = "",
    ) -> dict[str, Any]:
        if not name or not str(name).strip():
            raise ValueError("branch name is required")
        return {
            "name": name.strip(),
            "address": address,
            "schedule": schedule or {"mon-fri": "09:00-20:00"},
            "employees": [],
            "rooms": [],
            "equipment": [],
            "warehouse_ref": "enterprise_warehouse",
            "cash_register_ref": "enterprise_finance_cash",
            "uses_enterprise_services": True,
        }
