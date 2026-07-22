# Payment Engine — payments, installments, refunds, outstanding.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.finance.events import PaymentReceivedEvent
from applications.port_erp.finance.models import InvoiceStatus, Payment, PaymentStatus
from applications.port_erp.invoices.engine import InvoiceEngine, invoice_engine
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class PaymentEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        invoices: InvoiceEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._invoices = invoices or invoice_engine

    async def pay(
        self,
        *,
        invoice_id: str,
        amount: float,
        method: str = "transfer",
        installment_no: int = 0,
        reference: str = "",
    ) -> Payment:
        invoice = self._invoices.get(invoice_id)
        if amount <= 0:
            raise ValidationError("amount must be positive")
        outstanding = round(invoice.total - invoice.amount_paid, 2)
        if amount > outstanding + 0.001:
            raise ValidationError("payment exceeds outstanding balance")
        payment = Payment(
            invoice_id=invoice_id,
            customer_id=invoice.customer_id,
            amount=amount,
            currency=invoice.currency,
            status=PaymentStatus.COMPLETED,
            method=method,
            installment_no=installment_no,
            reference=reference,
        )
        saved = self._store.payments.save(payment.payment_id, payment)
        invoice.amount_paid = round(invoice.amount_paid + amount, 2)
        if invoice.amount_paid >= invoice.total:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        self._store.commercial_invoices.save(invoice.invoice_id, invoice)
        await publish(
            PaymentReceivedEvent(
                payment_id=saved.payment_id, invoice_id=invoice_id, amount=amount
            )
        )
        return saved

    def refund(self, payment_id: str, *, amount: float | None = None) -> Payment:
        original = self._store.payments.get(payment_id)
        if original is None:
            raise NotFoundError("Payment", payment_id)
        refund_amount = amount if amount is not None else original.amount
        if refund_amount <= 0 or refund_amount > original.amount:
            raise ValidationError("invalid refund amount")
        invoice = self._invoices.get(original.invoice_id)
        invoice.amount_paid = max(0.0, round(invoice.amount_paid - refund_amount, 2))
        invoice.status = (
            InvoiceStatus.PARTIALLY_PAID if invoice.amount_paid > 0 else InvoiceStatus.ISSUED
        )
        self._store.commercial_invoices.save(invoice.invoice_id, invoice)
        refund = Payment(
            invoice_id=original.invoice_id,
            customer_id=original.customer_id,
            amount=refund_amount,
            currency=original.currency,
            status=PaymentStatus.REFUNDED,
            method=original.method,
            is_refund=True,
            reference=f"refund:{payment_id}",
        )
        original.status = PaymentStatus.REFUNDED
        self._store.payments.save(payment_id, original)
        return self._store.payments.save(refund.payment_id, refund)

    def list_payments(self, *, invoice_id: str | None = None) -> list[Payment]:
        items = self._store.payments.list_all()
        if invoice_id:
            items = [p for p in items if p.invoice_id == invoice_id]
        return items


payment_engine = PaymentEngine()
