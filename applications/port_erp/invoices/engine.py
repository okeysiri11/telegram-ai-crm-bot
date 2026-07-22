# Invoice Engine — commercial invoices, credit/debit notes.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.currencies.engine import TaxEngine, tax_engine
from applications.port_erp.finance.events import InvoiceIssuedEvent
from applications.port_erp.finance.models import (
    ChargeLine,
    CommercialInvoice,
    CreditNote,
    DebitNote,
    FeeType,
    InvoiceStatus,
)
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Invoice
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.tariffs.commercial import CommercialTariffEngine, commercial_tariff_engine


class InvoiceEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        tariffs: CommercialTariffEngine | None = None,
        taxes: TaxEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._tariffs = tariffs or commercial_tariff_engine
        self._taxes = taxes or tax_engine

    def create(self, invoice: CommercialInvoice) -> CommercialInvoice:
        if not invoice.customer_id:
            raise ValidationError("customer_id is required")
        self._recompute(invoice)
        saved = self._store.commercial_invoices.save(invoice.invoice_id, invoice)
        # Keep foundation Invoice mirror for legacy billing_service compatibility
        self._store.invoices.save(
            saved.invoice_id,
            Invoice(
                invoice_id=saved.invoice_id,
                customer_id=saved.customer_id,
                amount=saved.total,
                currency=saved.currency,
                status=saved.status.value,
                description=saved.description,
            ),
        )
        return saved

    def get(self, invoice_id: str) -> CommercialInvoice:
        item = self._store.commercial_invoices.get(invoice_id)
        if item is None:
            raise NotFoundError("CommercialInvoice", invoice_id)
        return item

    def list_invoices(self, *, customer_id: str | None = None) -> list[CommercialInvoice]:
        items = self._store.commercial_invoices.list_all()
        if customer_id:
            items = [i for i in items if i.customer_id == customer_id]
        return items

    def add_charge(
        self,
        invoice_id: str,
        *,
        fee_type: FeeType | str,
        quantity: float = 1.0,
        description: str = "",
        terminal_id: str = "",
        country: str = "",
    ) -> CommercialInvoice:
        invoice = self.get(invoice_id)
        quote = self._tariffs.quote(fee_type=fee_type, quantity=quantity, terminal_id=terminal_id)
        tax = self._taxes.calculate(quote["amount"], country=country)
        line = ChargeLine(
            fee_type=FeeType(fee_type) if isinstance(fee_type, str) else fee_type,
            description=description or quote["fee_type"],
            quantity=quantity,
            unit_rate=quote["unit_rate"],
            amount=quote["amount"],
            tariff_id=quote["tariff_id"],
            tax_amount=tax["tax_amount"],
        )
        invoice.lines.append(line)
        self._recompute(invoice)
        return self._store.commercial_invoices.save(invoice_id, invoice)

    async def issue(self, invoice_id: str, *, due_in_days: float = 30.0) -> CommercialInvoice:
        invoice = self.get(invoice_id)
        if not invoice.lines and invoice.total <= 0:
            raise ValidationError("invoice has no charges")
        invoice.status = InvoiceStatus.ISSUED
        invoice.issued_at = time.time()
        invoice.due_at = invoice.issued_at + due_in_days * 86400
        saved = self._store.commercial_invoices.save(invoice_id, invoice)
        legacy = self._store.invoices.get(invoice_id)
        if legacy:
            legacy.status = "issued"
            legacy.amount = saved.total
            self._store.invoices.save(invoice_id, legacy)
        await publish(
            InvoiceIssuedEvent(
                invoice_id=invoice_id,
                customer_id=saved.customer_id,
                total=saved.total,
                currency=saved.currency,
            )
        )
        return saved

    def credit_note(self, note: CreditNote) -> CreditNote:
        invoice = self.get(note.invoice_id)
        if note.amount <= 0:
            raise ValidationError("amount must be positive")
        invoice.status = InvoiceStatus.CREDITED
        invoice.amount_paid = min(invoice.total, invoice.amount_paid + note.amount)
        self._store.commercial_invoices.save(invoice.invoice_id, invoice)
        return self._store.credit_notes.save(note.note_id, note)

    def debit_note(self, note: DebitNote) -> DebitNote:
        invoice = self.get(note.invoice_id)
        if note.amount <= 0:
            raise ValidationError("amount must be positive")
        invoice.total = round(invoice.total + note.amount, 2)
        invoice.subtotal = round(invoice.subtotal + note.amount, 2)
        if invoice.amount_paid < invoice.total:
            invoice.status = (
                InvoiceStatus.PARTIALLY_PAID if invoice.amount_paid > 0 else InvoiceStatus.ISSUED
            )
        self._store.commercial_invoices.save(invoice.invoice_id, invoice)
        return self._store.debit_notes.save(note.note_id, note)

    def outstanding(self, *, customer_id: str | None = None) -> list[CommercialInvoice]:
        items = [
            i
            for i in self.list_invoices(customer_id=customer_id)
            if i.status
            in (InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE)
            and i.total > i.amount_paid
        ]
        return items

    def _recompute(self, invoice: CommercialInvoice) -> None:
        invoice.subtotal = round(sum(line.amount for line in invoice.lines), 2)
        invoice.tax_total = round(sum(line.tax_amount for line in invoice.lines), 2)
        invoice.total = round(invoice.subtotal + invoice.tax_total, 2)


invoice_engine = InvoiceEngine()
