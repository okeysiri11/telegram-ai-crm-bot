"""Cash management — register, operations, reconciliation, petty cash, branches."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CashManagement:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def open_register(
        self, *, name: str, branch: str = "", currency: str = "USD", opening_balance: float = 0.0
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("register name required")
        rid = _id("pay_reg")
        return self.store.pay_cash_registers.save(
            rid,
            {
                "register_id": rid,
                "name": name,
                "branch": branch or "HQ",
                "currency": currency.upper(),
                "balance": float(opening_balance),
                "status": "open",
                "created_at": _now(),
            },
        )

    def operate(
        self, *, register_id: str, operation: str, amount: float, memo: str = ""
    ) -> dict[str, Any]:
        reg = self.store.pay_cash_registers.get(register_id)
        if reg is None:
            raise NotFoundError("cash_register", register_id)
        op = operation.lower().strip()
        if op not in ("in", "out", "petty"):
            raise ValidationError("operation must be one of ['in', 'out', 'petty']")
        amt = abs(float(amount))
        if amt <= 0:
            raise ValidationError("amount must be positive")
        bal = float(reg["balance"])
        if op in ("out", "petty") and bal < amt:
            raise ValidationError("insufficient cash balance")
        new_bal = bal + amt if op == "in" else bal - amt
        reg["balance"] = new_bal
        reg["updated_at"] = _now()
        self.store.pay_cash_registers.save(register_id, reg)
        oid = _id("pay_cop")
        return self.store.pay_cash_ops.save(
            oid,
            {
                "operation_id": oid,
                "register_id": register_id,
                "operation": op,
                "amount": amt,
                "balance_after": new_bal,
                "memo": memo,
                "at": _now(),
            },
        )

    def reconcile(
        self, *, register_id: str, counted_balance: float, note: str = ""
    ) -> dict[str, Any]:
        reg = self.store.pay_cash_registers.get(register_id)
        if reg is None:
            raise NotFoundError("cash_register", register_id)
        book = float(reg["balance"])
        counted = float(counted_balance)
        rid = _id("pay_crec")
        return self.store.pay_cash_recons.save(
            rid,
            {
                "reconciliation_id": rid,
                "register_id": register_id,
                "book_balance": book,
                "counted_balance": counted,
                "variance": round(counted - book, 6),
                "note": note,
                "at": _now(),
            },
        )

    def track_flow(self, *, register_id: str, period: str = "daily") -> dict[str, Any]:
        if self.store.pay_cash_registers.get(register_id) is None:
            raise NotFoundError("cash_register", register_id)
        ops = [o for o in self.store.pay_cash_ops.list_all() if o["register_id"] == register_id]
        inflow = sum(o["amount"] for o in ops if o["operation"] == "in")
        outflow = sum(o["amount"] for o in ops if o["operation"] in ("out", "petty"))
        fid = _id("pay_flow")
        return self.store.pay_cash_flows.save(
            fid,
            {
                "flow_id": fid,
                "register_id": register_id,
                "period": period,
                "inflow": inflow,
                "outflow": outflow,
                "net": round(inflow - outflow, 6),
                "at": _now(),
            },
        )

    def branch_account(
        self, *, branch: str, name: str, currency: str = "USD"
    ) -> dict[str, Any]:
        if not branch or not name:
            raise ValidationError("branch and name required")
        bid = _id("pay_br")
        return self.store.pay_branch_cash.save(
            bid,
            {
                "branch_account_id": bid,
                "branch": branch,
                "name": name,
                "currency": currency.upper(),
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "registers": self.store.pay_cash_registers.count(),
            "operations": self.store.pay_cash_ops.count(),
            "reconciliations": self.store.pay_cash_recons.count(),
            "flows": self.store.pay_cash_flows.count(),
            "branch_accounts": self.store.pay_branch_cash.count(),
        }
