# Payment operations — tracking, authorization, capture, multi-currency.

from __future__ import annotations

from events.publisher import publish

from applications.auto_marketplace.finance.ai_assistant import FinanceAIAssistant, finance_ai_assistant
from applications.auto_marketplace.finance.events import PaymentCompletedEvent
from applications.auto_marketplace.finance.models import FinancePayment, PaymentMethod, PaymentMethodType, Transaction, TransactionType, encrypt_field
from applications.auto_marketplace.finance.security import FinanceSecurity, finance_security
from applications.auto_marketplace.finance.workflow_bridge import FinanceWorkflowBridge, finance_workflow_bridge
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

_CURRENCY_RATES = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79}


class PaymentOperationsService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        ai: FinanceAIAssistant | None = None,
        security: FinanceSecurity | None = None,
        workflow: FinanceWorkflowBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._ai = ai or finance_ai_assistant
        self._security = security or finance_security
        self._workflow = workflow or finance_workflow_bridge

    def add_payment_method(self, method: PaymentMethod, *, raw_token: str = "") -> PaymentMethod:
        if raw_token:
            method.encrypted_token = encrypt_field(raw_token)
        return self._store.payment_methods.save(method.method_id, method)

    def get_payment_method(self, method_id: str) -> PaymentMethod:
        method = self._store.payment_methods.get(method_id)
        if method is None:
            raise NotFoundError("PaymentMethod", method_id)
        return method

    async def create_payment(self, payment: FinancePayment) -> FinancePayment:
        history = [p.to_dict() for p in self._store.finance_payments.list_all()[-20:]]
        anomaly = await self._ai.detect_payment_anomaly(payment, history)
        payment.metadata["anomaly_check"] = anomaly
        saved = self._store.finance_payments.save(payment.payment_id, payment)
        await self._workflow.payment_workflow(payment.payment_id)
        self._security.audit(action="create", actor_id="system", resource_type="payment", resource_id=payment.payment_id)
        return saved

    def get_payment(self, payment_id: str) -> FinancePayment:
        payment = self._store.finance_payments.get(payment_id)
        if payment is None:
            raise NotFoundError("FinancePayment", payment_id)
        return payment

    def list_payments(self, *, deal_id: str = "", customer_id: str = "") -> list[FinancePayment]:
        items = self._store.finance_payments.list_all()
        if deal_id:
            items = [p for p in items if p.deal_id == deal_id]
        if customer_id:
            items = [p for p in items if p.customer_id == customer_id]
        return items

    async def authorize(self, payment_id: str) -> FinancePayment:
        payment = self.get_payment(payment_id)
        payment.status = "authorized"
        return self._store.finance_payments.save(payment_id, payment)

    async def capture(self, payment_id: str) -> FinancePayment:
        payment = self.get_payment(payment_id)
        payment.status = "completed"
        txn = Transaction(
            transaction_type=TransactionType.PAYMENT,
            payment_id=payment_id,
            amount=payment.amount,
            currency=payment.currency,
            reference=f"txn-{payment_id[:8]}",
        )
        payment.transaction_id = txn.transaction_id
        self._store.transactions.save(txn.transaction_id, txn)
        saved = self._store.finance_payments.save(payment_id, payment)
        self._security.audit(action="capture", actor_id="system", resource_type="payment", resource_id=payment_id)
        await publish(
            PaymentCompletedEvent(
                payment_id=payment_id,
                deal_id=payment.deal_id,
                amount=payment.amount,
                currency=payment.currency,
            )
        )
        return saved

    @staticmethod
    def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
        usd = amount / _CURRENCY_RATES.get(from_currency, 1.0)
        return round(usd * _CURRENCY_RATES.get(to_currency, 1.0), 2)


payment_operations_service = PaymentOperationsService()
