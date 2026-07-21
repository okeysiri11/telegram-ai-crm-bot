# PaymentService — order payments.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from applications.agro_marketplace.shared.store import AgroStore, agro_store


@dataclass
class AgroPayment:
    payment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: str = "pending"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at,
        }


class PaymentService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def create_payment(self, payment: AgroPayment) -> AgroPayment:
        return self._store.payments.save(payment.payment_id, payment)

    def capture_payment(self, payment_id: str) -> AgroPayment | None:
        payment = self._store.payments.get(payment_id)
        if payment is None:
            return None
        payment.status = "captured"
        return self._store.payments.save(payment_id, payment)

    def list_payments(self) -> list[AgroPayment]:
        return self._store.payments.list_all()


payment_service = PaymentService()
