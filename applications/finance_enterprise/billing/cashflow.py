"""Cash flow intelligence — receipts, payments, forecasts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CashFlowIntelligence:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def expected_receipts(self, *, amount: float, due_on: str, source_ref: str = "") -> dict[str, Any]:
        if float(amount) <= 0:
            raise ValidationError("amount must be positive")
        rid = _id("bil_rcpt")
        return self.store.bil_expected_receipts.save(
            rid,
            {
                "receipt_id": rid,
                "amount": float(amount),
                "due_on": due_on,
                "source_ref": source_ref,
                "at": _now(),
            },
        )

    def expected_payments(self, *, amount: float, due_on: str, source_ref: str = "") -> dict[str, Any]:
        if float(amount) <= 0:
            raise ValidationError("amount must be positive")
        pid = _id("bil_epay")
        return self.store.bil_expected_payments.save(
            pid,
            {
                "payment_id": pid,
                "amount": float(amount),
                "due_on": due_on,
                "source_ref": source_ref,
                "at": _now(),
            },
        )

    def forecast(self, *, horizon_days: int = 30, kind: str = "cash") -> dict[str, Any]:
        kind_l = kind.lower().strip()
        if kind_l not in ("cash", "collection", "liquidity"):
            raise ValidationError("kind must be one of ['cash', 'collection', 'liquidity']")
        receipts = sum(float(r["amount"]) for r in self.store.bil_expected_receipts.list_all())
        payments = sum(float(p["amount"]) for p in self.store.bil_expected_payments.list_all())
        fid = _id("bil_fc")
        return self.store.bil_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "kind": kind_l,
                "horizon_days": max(1, int(horizon_days)),
                "expected_receipts": receipts,
                "expected_payments": payments,
                "net": round(receipts - payments, 6),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "expected_receipts": self.store.bil_expected_receipts.count(),
            "expected_payments": self.store.bil_expected_payments.count(),
            "forecasts": self.store.bil_forecasts.count(),
        }
