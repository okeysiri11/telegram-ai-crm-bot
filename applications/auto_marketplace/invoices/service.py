# Invoice service — generation, approval, multi-currency.

from __future__ import annotations

from events.publisher import publish

from applications.auto_marketplace.finance.events import InvoiceGeneratedEvent
from applications.auto_marketplace.finance.models import FinanceInvoice, InvoiceStatus
from applications.auto_marketplace.finance.security import FinanceSecurity, finance_security
from applications.auto_marketplace.finance.workflow_bridge import FinanceWorkflowBridge, finance_workflow_bridge
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.taxes.service import TaxService, tax_service


class InvoiceService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        taxes: TaxService | None = None,
        security: FinanceSecurity | None = None,
        workflow: FinanceWorkflowBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._taxes = taxes or tax_service
        self._security = security or finance_security
        self._workflow = workflow or finance_workflow_bridge

    async def generate(
        self,
        *,
        deal_id: str,
        customer_id: str,
        dealer_id: str = "",
        amount: float,
        currency: str = "USD",
        line_items: list[dict] | None = None,
        jurisdiction: str = "US",
    ) -> FinanceInvoice:
        tax_record = self._taxes.calculate(deal_id=deal_id, taxable_amount=amount, jurisdiction=jurisdiction, currency=currency)
        invoice = FinanceInvoice(
            deal_id=deal_id,
            customer_id=customer_id,
            dealer_id=dealer_id,
            amount=amount,
            tax_amount=tax_record.tax_amount,
            total_amount=round(amount + tax_record.tax_amount, 2),
            currency=currency,
            line_items=line_items or [{"description": "Vehicle purchase", "amount": amount}],
            status=InvoiceStatus.DRAFT,
        )
        invoice.pdf_url = f"/invoices/{invoice.invoice_id}.pdf"
        self._store.finance_invoices.save(invoice.invoice_id, invoice)
        invoice.tax_amount = tax_record.tax_amount
        tax_record.invoice_id = invoice.invoice_id
        self._security.audit(action="generate", actor_id="system", resource_type="invoice", resource_id=invoice.invoice_id)
        await publish(
            InvoiceGeneratedEvent(
                invoice_id=invoice.invoice_id,
                deal_id=deal_id,
                total_amount=invoice.total_amount,
                currency=currency,
            )
        )
        return invoice

    def get(self, invoice_id: str) -> FinanceInvoice:
        invoice = self._store.finance_invoices.get(invoice_id)
        if invoice is None:
            raise NotFoundError("FinanceInvoice", invoice_id)
        return invoice

    def list_invoices(self, *, customer_id: str = "", deal_id: str = "") -> list[FinanceInvoice]:
        items = self._store.finance_invoices.list_all()
        if customer_id:
            items = [i for i in items if i.customer_id == customer_id]
        if deal_id:
            items = [i for i in items if i.deal_id == deal_id]
        return items

    async def submit_for_approval(self, invoice_id: str, *, approver_id: str) -> FinanceInvoice:
        invoice = self.get(invoice_id)
        invoice.status = InvoiceStatus.PENDING_APPROVAL
        workflow_id = await self._workflow.invoice_approval(invoice_id, approver_id)
        invoice.document_id = workflow_id or ""
        self._store.finance_invoices.save(invoice_id, invoice)
        return invoice

    def approve(self, invoice_id: str) -> FinanceInvoice:
        invoice = self.get(invoice_id)
        invoice.status = InvoiceStatus.APPROVED
        return self._store.finance_invoices.save(invoice_id, invoice)

    def mark_paid(self, invoice_id: str, *, payment_id: str) -> FinanceInvoice:
        invoice = self.get(invoice_id)
        invoice.status = InvoiceStatus.PAID
        invoice.payment_id = payment_id
        return self._store.finance_invoices.save(invoice_id, invoice)


invoice_service = InvoiceService()
