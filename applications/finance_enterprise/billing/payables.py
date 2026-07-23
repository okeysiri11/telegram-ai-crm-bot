"""Accounts payable — bills, scheduling, approvals, liabilities, vendor statements."""

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


class AccountsPayable:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def register_bill(
        self,
        *,
        vendor_ref: str,
        amount: float,
        currency: str = "USD",
        due_on: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        if not vendor_ref:
            raise ValidationError("vendor_ref required")
        if float(amount) <= 0:
            raise ValidationError("amount must be positive")
        bid = _id("bil_bill")
        return self.store.bil_bills.save(
            bid,
            {
                "bill_id": bid,
                "vendor_ref": vendor_ref,
                "amount": float(amount),
                "outstanding": float(amount),
                "currency": currency.upper(),
                "due_on": due_on,
                "description": description,
                "status": "open",
                "created_at": _now(),
            },
        )

    def schedule_payment(self, *, bill_id: str, schedule_at: str, amount: float | None = None) -> dict[str, Any]:
        bill = self.store.bil_bills.get(bill_id)
        if bill is None:
            raise NotFoundError("bill", bill_id)
        if not schedule_at:
            raise ValidationError("schedule_at required")
        sid = _id("bil_sch")
        return self.store.bil_ap_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "bill_id": bill_id,
                "schedule_at": schedule_at,
                "amount": float(amount if amount is not None else bill["outstanding"]),
                "status": "scheduled",
                "at": _now(),
            },
        )

    def approve(self, *, bill_id: str, approver: str, decision: str = "approved") -> dict[str, Any]:
        bill = self.store.bil_bills.get(bill_id)
        if bill is None:
            raise NotFoundError("bill", bill_id)
        dec = decision.lower().strip()
        if dec not in ("approved", "rejected"):
            raise ValidationError("decision must be approved or rejected")
        aid = _id("bil_apapr")
        bill["status"] = dec
        bill["updated_at"] = _now()
        self.store.bil_bills.save(bill_id, bill)
        return self.store.bil_ap_approvals.save(
            aid,
            {
                "approval_id": aid,
                "bill_id": bill_id,
                "approver": approver,
                "decision": dec,
                "at": _now(),
            },
        )

    def liabilities(self) -> dict[str, Any]:
        open_bills = [b for b in self.store.bil_bills.list_all() if b.get("status") in ("open", "approved")]
        total = sum(float(b.get("outstanding", 0)) for b in open_bills)
        lid = _id("bil_liab")
        return self.store.bil_liabilities.save(
            lid,
            {
                "liability_id": lid,
                "bill_count": len(open_bills),
                "total_outstanding": total,
                "at": _now(),
            },
        )

    def reconcile_statement(
        self, *, vendor_ref: str, statement_total: float, note: str = ""
    ) -> dict[str, Any]:
        if not vendor_ref:
            raise ValidationError("vendor_ref required")
        books = sum(
            float(b.get("outstanding", 0))
            for b in self.store.bil_bills.list_all()
            if b["vendor_ref"] == vendor_ref
        )
        rid = _id("bil_vrec")
        return self.store.bil_vendor_recons.save(
            rid,
            {
                "reconciliation_id": rid,
                "vendor_ref": vendor_ref,
                "books_total": books,
                "statement_total": float(statement_total),
                "variance": round(float(statement_total) - books, 6),
                "note": note,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "bills": self.store.bil_bills.count(),
            "schedules": self.store.bil_ap_schedules.count(),
            "approvals": self.store.bil_ap_approvals.count(),
            "liabilities": self.store.bil_liabilities.count(),
            "vendor_recons": self.store.bil_vendor_recons.count(),
        }
