# Transaction Payments — invoices, deposits, refunds, installments, multi-currency.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.models import TransactionPayment


class TransactionPaymentEngine:
    SUPPORTED_CURRENCIES = ("USD", "EUR", "GBP", "AED", "TRY")

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create(
        self,
        *,
        transaction_id: str,
        amount: float,
        kind: str = "invoice",
        currency: str = "USD",
        installment_no: int = 0,
    ) -> TransactionPayment:
        if amount <= 0:
            raise ValidationError("amount must be positive")
        if currency not in self.SUPPORTED_CURRENCIES:
            raise ValidationError(f"unsupported currency: {currency}")
        payment = TransactionPayment(
            transaction_id=transaction_id,
            kind=kind,
            amount=amount,
            currency=currency,
            installment_no=installment_no,
            history=[{"event": "created", "at": time.time()}],
        )
        return self._store.transaction_payments.save(payment.payment_id, payment)

    def get(self, payment_id: str) -> TransactionPayment:
        payment = self._store.transaction_payments.get(payment_id)
        if payment is None:
            raise NotFoundError("TransactionPayment", payment_id)
        return payment

    def capture(self, payment_id: str) -> TransactionPayment:
        payment = self.get(payment_id)
        payment.status = "captured"
        payment.history.append({"event": "captured", "at": time.time()})
        return self._store.transaction_payments.save(payment_id, payment)

    def refund(self, payment_id: str, amount: float | None = None) -> TransactionPayment:
        payment = self.get(payment_id)
        refund_amount = amount if amount is not None else payment.amount
        payment.status = "refunded"
        payment.history.append({"event": "refunded", "amount": refund_amount, "at": time.time()})
        return self._store.transaction_payments.save(payment_id, payment)

    def schedule_installments(
        self, *, transaction_id: str, total: float, count: int = 3, currency: str = "USD"
    ) -> list[TransactionPayment]:
        if count < 2:
            raise ValidationError("installment count must be >= 2")
        part = round(total / count, 2)
        items = []
        for i in range(1, count + 1):
            amt = part if i < count else round(total - part * (count - 1), 2)
            items.append(
                self.create(
                    transaction_id=transaction_id,
                    amount=amt,
                    kind="installment",
                    currency=currency,
                    installment_no=i,
                )
            )
        return items

    def history(self, *, transaction_id: str = "") -> list[TransactionPayment]:
        items = self._store.transaction_payments.list_all()
        if transaction_id:
            items = [p for p in items if p.transaction_id == transaction_id]
        return items

    def metrics(self) -> dict:
        return {
            "transaction_payments": self._store.transaction_payments.count(),
            "currencies": list(self.SUPPORTED_CURRENCIES),
        }


transaction_payment_engine = TransactionPaymentEngine()
