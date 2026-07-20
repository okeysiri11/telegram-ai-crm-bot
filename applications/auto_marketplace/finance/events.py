# Finance events — Sprint 6.5.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class DocumentCreatedEvent(BaseEvent):
    document_id: str = ""
    category: str = ""
    customer_id: str = ""


@dataclass(kw_only=True)
class ContractSignedEvent(BaseEvent):
    contract_id: str = ""
    contract_type: str = ""
    customer_id: str = ""
    amount: float = 0.0


@dataclass(kw_only=True)
class InvoiceGeneratedEvent(BaseEvent):
    invoice_id: str = ""
    deal_id: str = ""
    total_amount: float = 0.0
    currency: str = "USD"


@dataclass(kw_only=True)
class PaymentCompletedEvent(BaseEvent):
    payment_id: str = ""
    deal_id: str = ""
    amount: float = 0.0
    currency: str = "USD"


@dataclass(kw_only=True)
class RefundProcessedEvent(BaseEvent):
    refund_id: str = ""
    payment_id: str = ""
    amount: float = 0.0


@dataclass(kw_only=True)
class SettlementCompletedEvent(BaseEvent):
    settlement_id: str = ""
    dealer_id: str = ""
    net_amount: float = 0.0
