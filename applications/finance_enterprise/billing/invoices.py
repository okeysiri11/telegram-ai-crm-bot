"""Invoice management — registry, generator, proforma, recurring, credit/debit notes."""

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


class InvoiceManagement:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.invoice_types = list(DEFAULT_CONFIG.bil_invoice_types)
        self._seq = 1000

    def _next_number(self, prefix: str = "INV") -> str:
        self._seq += 1
        return f"{prefix}-{self._seq}"

    def create_template(self, *, name: str, body: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("template name required")
        tid = _id("bil_tpl")
        return self.store.bil_templates.save(
            tid,
            {
                "template_id": tid,
                "name": name,
                "body": body or "Standard invoice template",
                "created_at": _now(),
            },
        )

    def create_invoice(
        self,
        *,
        customer_ref: str,
        amount: float,
        currency: str = "USD",
        invoice_type: str = "standard",
        tax_amount: float = 0.0,
        due_on: str = "",
        template_id: str = "",
        lines: list[dict[str, Any]] | None = None,
        recurrence: str = "",
    ) -> dict[str, Any]:
        it = invoice_type.lower().strip()
        if it not in self.invoice_types:
            raise ValidationError(f"invoice_type must be one of {self.invoice_types}")
        if not customer_ref:
            raise ValidationError("customer_ref required")
        amt = float(amount)
        if amt < 0:
            raise ValidationError("amount must be non-negative")
        iid = _id("bil_inv")
        number = self._next_number("PRF" if it == "proforma" else "INV")
        return self.store.bil_invoices.save(
            iid,
            {
                "invoice_id": iid,
                "invoice_number": number,
                "invoice_type": it,
                "customer_ref": customer_ref,
                "amount": amt,
                "tax_amount": float(tax_amount),
                "total": round(amt + float(tax_amount), 6),
                "currency": currency.upper(),
                "due_on": due_on,
                "template_id": template_id,
                "lines": lines or [],
                "recurrence": recurrence,
                "status": "draft",
                "created_at": _now(),
            },
        )

    def credit_note(self, *, invoice_id: str, amount: float, reason: str = "") -> dict[str, Any]:
        inv = self.store.bil_invoices.get(invoice_id)
        if inv is None:
            raise NotFoundError("invoice", invoice_id)
        cid = _id("bil_cn")
        return self.store.bil_credit_notes.save(
            cid,
            {
                "credit_note_id": cid,
                "invoice_id": invoice_id,
                "amount": float(amount),
                "reason": reason or "credit adjustment",
                "number": self._next_number("CN"),
                "created_at": _now(),
            },
        )

    def debit_note(self, *, invoice_id: str, amount: float, reason: str = "") -> dict[str, Any]:
        inv = self.store.bil_invoices.get(invoice_id)
        if inv is None:
            raise NotFoundError("invoice", invoice_id)
        did = _id("bil_dn")
        return self.store.bil_debit_notes.save(
            did,
            {
                "debit_note_id": did,
                "invoice_id": invoice_id,
                "amount": float(amount),
                "reason": reason or "debit adjustment",
                "number": self._next_number("DN"),
                "created_at": _now(),
            },
        )

    def issue(self, *, invoice_id: str) -> dict[str, Any]:
        inv = self.store.bil_invoices.get(invoice_id)
        if inv is None:
            raise NotFoundError("invoice", invoice_id)
        inv["status"] = "issued"
        inv["issued_at"] = _now()
        return self.store.bil_invoices.save(invoice_id, inv)

    def status(self) -> dict[str, Any]:
        return {
            "invoices": self.store.bil_invoices.count(),
            "templates": self.store.bil_templates.count(),
            "credit_notes": self.store.bil_credit_notes.count(),
            "debit_notes": self.store.bil_debit_notes.count(),
            "types": self.invoice_types,
        }
