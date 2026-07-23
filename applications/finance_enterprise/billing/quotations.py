"""Quotation management — generate, approve, convert to invoice."""

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


class QuotationManagement:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def create_template(self, *, name: str, body: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("template name required")
        tid = _id("bil_qtpl")
        return self.store.bil_quote_templates.save(
            tid,
            {"template_id": tid, "name": name, "body": body or "Quotation template", "created_at": _now()},
        )

    def create(
        self,
        *,
        customer_ref: str,
        amount: float,
        currency: str = "USD",
        template_id: str = "",
        valid_until: str = "",
    ) -> dict[str, Any]:
        if not customer_ref:
            raise ValidationError("customer_ref required")
        if float(amount) < 0:
            raise ValidationError("amount must be non-negative")
        qid = _id("bil_quo")
        return self.store.bil_quotations.save(
            qid,
            {
                "quotation_id": qid,
                "customer_ref": customer_ref,
                "amount": float(amount),
                "currency": currency.upper(),
                "template_id": template_id,
                "valid_until": valid_until,
                "status": "draft",
                "created_at": _now(),
            },
        )

    def approve(self, *, quotation_id: str, approver: str = "sales") -> dict[str, Any]:
        quote = self.store.bil_quotations.get(quotation_id)
        if quote is None:
            raise NotFoundError("quotation", quotation_id)
        quote["status"] = "approved"
        quote["approver"] = approver
        quote["approved_at"] = _now()
        self.store.bil_quotations.save(quotation_id, quote)
        hid = _id("bil_qh")
        return self.store.bil_quote_history.save(
            hid,
            {
                "history_id": hid,
                "quotation_id": quotation_id,
                "event": "approved",
                "actor": approver,
                "at": _now(),
            },
        )

    def convert_to_invoice(self, *, quotation_id: str, invoices: Any) -> dict[str, Any]:
        quote = self.store.bil_quotations.get(quotation_id)
        if quote is None:
            raise NotFoundError("quotation", quotation_id)
        invoice = invoices.create_invoice(
            customer_ref=quote["customer_ref"],
            amount=quote["amount"],
            currency=quote["currency"],
            invoice_type="standard",
        )
        invoices.issue(invoice_id=invoice["invoice_id"])
        quote["status"] = "converted"
        quote["invoice_id"] = invoice["invoice_id"]
        quote["converted_at"] = _now()
        self.store.bil_quotations.save(quotation_id, quote)
        return {"quotation_id": quotation_id, "invoice_id": invoice["invoice_id"], "status": "converted"}

    def status(self) -> dict[str, Any]:
        return {
            "quotations": self.store.bil_quotations.count(),
            "templates": self.store.bil_quote_templates.count(),
            "history": self.store.bil_quote_history.count(),
        }
