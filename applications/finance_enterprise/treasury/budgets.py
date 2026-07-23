"""Budget management — registry, dept/project/cost center, approval, revisions."""

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


class BudgetManagement:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.budget_types = list(DEFAULT_CONFIG.tr_budget_types)

    def create_budget(
        self,
        *,
        name: str,
        budget_type: str,
        amount: float,
        period: str = "2026",
        owner_ref: str = "",
        currency: str = "USD",
    ) -> dict[str, Any]:
        bt = budget_type.lower().strip()
        if bt not in self.budget_types:
            raise ValidationError(f"budget_type must be one of {self.budget_types}")
        if not name:
            raise ValidationError("name required")
        if float(amount) < 0:
            raise ValidationError("amount must be non-negative")
        bid = _id("tr_bud")
        return self.store.tr_budgets.save(
            bid,
            {
                "budget_id": bid,
                "name": name,
                "budget_type": bt,
                "amount": float(amount),
                "period": period,
                "owner_ref": owner_ref,
                "currency": currency.upper(),
                "status": "draft",
                "created_at": _now(),
            },
        )

    def approve(self, *, budget_id: str, approver: str = "cfo") -> dict[str, Any]:
        bud = self.store.tr_budgets.get(budget_id)
        if bud is None:
            raise NotFoundError("budget", budget_id)
        bud["status"] = "approved"
        bud["approver"] = approver
        bud["approved_at"] = _now()
        self.store.tr_budgets.save(budget_id, bud)
        aid = _id("tr_bapr")
        return self.store.tr_budget_approvals.save(
            aid,
            {
                "approval_id": aid,
                "budget_id": budget_id,
                "approver": approver,
                "decision": "approved",
                "at": _now(),
            },
        )

    def revise(self, *, budget_id: str, new_amount: float, reason: str = "") -> dict[str, Any]:
        bud = self.store.tr_budgets.get(budget_id)
        if bud is None:
            raise NotFoundError("budget", budget_id)
        rid = _id("tr_brev")
        prev = float(bud["amount"])
        bud["amount"] = float(new_amount)
        bud["updated_at"] = _now()
        self.store.tr_budgets.save(budget_id, bud)
        return self.store.tr_budget_revisions.save(
            rid,
            {
                "revision_id": rid,
                "budget_id": budget_id,
                "previous_amount": prev,
                "new_amount": float(new_amount),
                "reason": reason or "budget revision",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "budgets": self.store.tr_budgets.count(),
            "approvals": self.store.tr_budget_approvals.count(),
            "revisions": self.store.tr_budget_revisions.count(),
            "types": self.budget_types,
        }
