"""Accounts receivable — balances, aging, collections, allocations."""

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


class AccountsReceivable:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def open_receivable(
        self, *, customer_ref: str, invoice_id: str, amount: float, currency: str = "USD"
    ) -> dict[str, Any]:
        if not customer_ref or not invoice_id:
            raise ValidationError("customer_ref and invoice_id required")
        if float(amount) <= 0:
            raise ValidationError("amount must be positive")
        rid = _id("bil_ar")
        return self.store.bil_receivables.save(
            rid,
            {
                "receivable_id": rid,
                "customer_ref": customer_ref,
                "invoice_id": invoice_id,
                "amount": float(amount),
                "outstanding": float(amount),
                "currency": currency.upper(),
                "status": "open",
                "created_at": _now(),
            },
        )

    def aging(self, *, customer_ref: str = "") -> dict[str, Any]:
        rows = self.store.bil_receivables.list_all()
        if customer_ref:
            rows = [r for r in rows if r["customer_ref"] == customer_ref]
        buckets = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "90_plus": 0.0}
        for r in rows:
            # Synthetic aging: put open outstanding into current unless marked overdue
            key = "90_plus" if r.get("overdue") else "current"
            buckets[key] += float(r.get("outstanding", 0))
        aid = _id("bil_age")
        return self.store.bil_aging.save(
            aid,
            {
                "aging_id": aid,
                "customer_ref": customer_ref or "*",
                "buckets": buckets,
                "total_outstanding": sum(buckets.values()),
                "at": _now(),
            },
        )

    def collect(self, *, receivable_id: str, step: str = "reminder") -> dict[str, Any]:
        ar = self.store.bil_receivables.get(receivable_id)
        if ar is None:
            raise NotFoundError("receivable", receivable_id)
        cid = _id("bil_col")
        return self.store.bil_collections.save(
            cid,
            {
                "collection_id": cid,
                "receivable_id": receivable_id,
                "step": step,
                "at": _now(),
            },
        )

    def allocate(
        self, *, receivable_id: str, amount: float, payment_ref: str = ""
    ) -> dict[str, Any]:
        ar = self.store.bil_receivables.get(receivable_id)
        if ar is None:
            raise NotFoundError("receivable", receivable_id)
        amt = float(amount)
        if amt <= 0:
            raise ValidationError("amount must be positive")
        if amt > float(ar["outstanding"]):
            raise ValidationError("allocation exceeds outstanding")
        ar["outstanding"] = round(float(ar["outstanding"]) - amt, 6)
        if ar["outstanding"] == 0:
            ar["status"] = "paid"
        ar["updated_at"] = _now()
        self.store.bil_receivables.save(receivable_id, ar)
        aid = _id("bil_alloc")
        return self.store.bil_allocations.save(
            aid,
            {
                "allocation_id": aid,
                "receivable_id": receivable_id,
                "amount": amt,
                "payment_ref": payment_ref,
                "outstanding_after": ar["outstanding"],
                "at": _now(),
            },
        )

    def mark_overdue(self, *, receivable_id: str) -> dict[str, Any]:
        ar = self.store.bil_receivables.get(receivable_id)
        if ar is None:
            raise NotFoundError("receivable", receivable_id)
        ar["overdue"] = True
        ar["status"] = "overdue"
        ar["updated_at"] = _now()
        return self.store.bil_receivables.save(receivable_id, ar)

    def status(self) -> dict[str, Any]:
        return {
            "receivables": self.store.bil_receivables.count(),
            "aging_reports": self.store.bil_aging.count(),
            "collections": self.store.bil_collections.count(),
            "allocations": self.store.bil_allocations.count(),
        }
