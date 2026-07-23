"""Payment engine — transfers, scheduled/recurring/bulk, status tracking."""

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


class PaymentEngine:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.payment_types = list(DEFAULT_CONFIG.pay_payment_types)
        self.statuses = list(DEFAULT_CONFIG.pay_payment_statuses)

    def create_payment(
        self,
        *,
        payment_type: str,
        amount: float,
        currency: str = "USD",
        from_ref: str = "",
        to_ref: str = "",
        schedule_at: str = "",
        recurrence: str = "",
        external_key: str = "",
    ) -> dict[str, Any]:
        pt = payment_type.lower().strip()
        if pt not in self.payment_types:
            raise ValidationError(f"payment_type must be one of {self.payment_types}")
        amt = float(amount)
        if amt <= 0:
            raise ValidationError("amount must be positive")
        if external_key:
            for existing in self.store.pay_payments.list_all():
                if existing.get("external_key") == external_key:
                    raise ValidationError(f"duplicate payment external_key: {external_key}")
        pid = _id("pay_pmt")
        status = "scheduled" if schedule_at or recurrence else "pending"
        return self.store.pay_payments.save(
            pid,
            {
                "payment_id": pid,
                "payment_type": pt,
                "amount": amt,
                "currency": currency.upper(),
                "from_ref": from_ref,
                "to_ref": to_ref,
                "schedule_at": schedule_at,
                "recurrence": recurrence,
                "external_key": external_key,
                "status": status,
                "created_at": _now(),
            },
        )

    def update_status(self, *, payment_id: str, status: str, detail: str = "") -> dict[str, Any]:
        payment = self.store.pay_payments.get(payment_id)
        if payment is None:
            raise NotFoundError("payment", payment_id)
        st = status.lower().strip()
        if st not in self.statuses:
            raise ValidationError(f"status must be one of {self.statuses}")
        payment["status"] = st
        payment["status_detail"] = detail
        payment["updated_at"] = _now()
        return self.store.pay_payments.save(payment_id, payment)

    def bulk(self, *, payments: list[dict[str, Any]]) -> dict[str, Any]:
        if not payments:
            raise ValidationError("payments list required")
        created = []
        for item in payments:
            created.append(
                self.create_payment(
                    payment_type=item.get("payment_type", "outgoing"),
                    amount=float(item.get("amount", 0) or 0),
                    currency=item.get("currency", "USD"),
                    from_ref=item.get("from_ref", ""),
                    to_ref=item.get("to_ref", ""),
                    external_key=item.get("external_key", ""),
                )
            )
        bid = _id("pay_bulk")
        return self.store.pay_bulk.save(
            bid,
            {
                "bulk_id": bid,
                "payment_ids": [p["payment_id"] for p in created],
                "count": len(created),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "payments": self.store.pay_payments.count(),
            "bulk_batches": self.store.pay_bulk.count(),
            "types": self.payment_types,
            "statuses": self.statuses,
        }
