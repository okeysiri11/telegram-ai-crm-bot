"""Financial planning — workspace, revenue/expense/capex/investment/working capital."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FinancialPlanning:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.plan_types = list(DEFAULT_CONFIG.tr_plan_types)

    def create_workspace(self, *, name: str, period: str = "2026") -> dict[str, Any]:
        if not name:
            raise ValidationError("workspace name required")
        wid = _id("tr_ws")
        return self.store.tr_workspaces.save(
            wid,
            {
                "workspace_id": wid,
                "name": name,
                "period": period,
                "created_at": _now(),
            },
        )

    def add_plan(
        self,
        *,
        workspace_id: str,
        plan_type: str,
        amount: float,
        label: str = "",
    ) -> dict[str, Any]:
        if self.store.tr_workspaces.get(workspace_id) is None:
            raise NotFoundError("workspace", workspace_id)
        pt = plan_type.lower().strip()
        if pt not in self.plan_types:
            raise ValidationError(f"plan_type must be one of {self.plan_types}")
        pid = _id("tr_plan")
        return self.store.tr_plans.save(
            pid,
            {
                "plan_id": pid,
                "workspace_id": workspace_id,
                "plan_type": pt,
                "amount": float(amount),
                "label": label or pt.replace("_", " ").title(),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "workspaces": self.store.tr_workspaces.count(),
            "plans": self.store.tr_plans.count(),
            "types": self.plan_types,
        }
