# PaymentService — payments and invoicing.

from __future__ import annotations

from applications.auto_marketplace.documents.service import DocumentService, document_service
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import Invoice, Payment, PaymentStatus
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PaymentService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        documents: DocumentService | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._documents = documents or document_service

    def create_payment(self, payment: Payment) -> Payment:
        return self._store.payments.save(payment.payment_id, payment)

    def get_payment(self, payment_id: str) -> Payment:
        payment = self._store.payments.get(payment_id)
        if payment is None:
            raise NotFoundError("Payment", payment_id)
        return payment

    def authorize_payment(self, payment_id: str) -> Payment:
        payment = self.get_payment(payment_id)
        payment.status = PaymentStatus.AUTHORIZED
        return self._store.payments.save(payment_id, payment)

    def capture_payment(self, payment_id: str) -> Payment:
        payment = self.get_payment(payment_id)
        payment.status = PaymentStatus.CAPTURED
        saved = self._store.payments.save(payment_id, payment)
        invoice = Invoice(
            deal_id=payment.deal_id,
            payment_id=payment_id,
            amount=payment.amount,
            currency=payment.currency,
        )
        self._documents.generate_invoice(invoice)
        return saved


payment_service = PaymentService()
