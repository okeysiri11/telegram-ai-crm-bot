"""Payment processing — authorization, approval, validation, recovery, notifications."""

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


class PaymentProcessing:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def authorize(self, *, payment_id: str, authorized_by: str = "treasury") -> dict[str, Any]:
        payment = self.store.pay_payments.get(payment_id)
        if payment is None:
            raise NotFoundError("payment", payment_id)
        aid = _id("pay_auth")
        payment["status"] = "authorized"
        payment["updated_at"] = _now()
        self.store.pay_payments.save(payment_id, payment)
        return self.store.pay_authorizations.save(
            aid,
            {
                "authorization_id": aid,
                "payment_id": payment_id,
                "authorized_by": authorized_by,
                "at": _now(),
            },
        )

    def approve(
        self, *, payment_id: str, approver: str, decision: str = "approved", note: str = ""
    ) -> dict[str, Any]:
        payment = self.store.pay_payments.get(payment_id)
        if payment is None:
            raise NotFoundError("payment", payment_id)
        dec = decision.lower().strip()
        if dec not in ("approved", "rejected"):
            raise ValidationError("decision must be approved or rejected")
        aid = _id("pay_apr")
        payment["status"] = dec
        payment["updated_at"] = _now()
        self.store.pay_payments.save(payment_id, payment)
        return self.store.pay_approvals.save(
            aid,
            {
                "approval_id": aid,
                "payment_id": payment_id,
                "approver": approver,
                "decision": dec,
                "note": note,
                "at": _now(),
            },
        )

    def validate_transaction(
        self, *, payment_id: str, checks: list[str] | None = None
    ) -> dict[str, Any]:
        payment = self.store.pay_payments.get(payment_id)
        if payment is None:
            raise NotFoundError("payment", payment_id)
        vid = _id("pay_val")
        return self.store.pay_validations.save(
            vid,
            {
                "validation_id": vid,
                "payment_id": payment_id,
                "checks": checks or ["amount", "currency", "counterparty"],
                "result": "pass",
                "at": _now(),
            },
        )

    def recover_failed(self, *, payment_id: str, reason: str = "") -> dict[str, Any]:
        payment = self.store.pay_payments.get(payment_id)
        if payment is None:
            raise NotFoundError("payment", payment_id)
        rid = _id("pay_rec")
        payment["status"] = "retrying"
        payment["updated_at"] = _now()
        self.store.pay_payments.save(payment_id, payment)
        return self.store.pay_recoveries.save(
            rid,
            {
                "recovery_id": rid,
                "payment_id": payment_id,
                "reason": reason or "failed payment recovery",
                "at": _now(),
            },
        )

    def notify(self, *, payment_id: str, channel: str = "email", message: str = "") -> dict[str, Any]:
        if self.store.pay_payments.get(payment_id) is None:
            raise NotFoundError("payment", payment_id)
        nid = _id("pay_ntf")
        return self.store.pay_notifications.save(
            nid,
            {
                "notification_id": nid,
                "payment_id": payment_id,
                "channel": channel,
                "message": message or f"Payment {payment_id} update",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "authorizations": self.store.pay_authorizations.count(),
            "approvals": self.store.pay_approvals.count(),
            "validations": self.store.pay_validations.count(),
            "recoveries": self.store.pay_recoveries.count(),
            "notifications": self.store.pay_notifications.count(),
        }
