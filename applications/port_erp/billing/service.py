# Port billing service.

from __future__ import annotations

from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Invoice
from applications.port_erp.shared.store import PortStore, port_store


class BillingService:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def create_invoice(self, invoice: Invoice) -> Invoice:
        if invoice.amount < 0:
            raise ValidationError("amount must be non-negative")
        return self._store.invoices.save(invoice.invoice_id, invoice)

    def get(self, invoice_id: str) -> Invoice:
        invoice = self._store.invoices.get(invoice_id)
        if invoice is None:
            raise NotFoundError("Invoice", invoice_id)
        return invoice

    def list_invoices(self, *, customer_id: str | None = None) -> list[Invoice]:
        items = self._store.invoices.list_all()
        if customer_id:
            items = [i for i in items if i.customer_id == customer_id]
        return items


billing_service = BillingService()
