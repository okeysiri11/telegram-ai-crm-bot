# Sprint 9.7 — Finance / commercial events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class InvoiceIssuedEvent(BaseEvent):
    invoice_id: str = ""
    customer_id: str = ""
    total: float = 0.0
    currency: str = ""


@dataclass(kw_only=True)
class PaymentReceivedEvent(BaseEvent):
    payment_id: str = ""
    invoice_id: str = ""
    amount: float = 0.0


@dataclass(kw_only=True)
class ContractActivatedEvent(BaseEvent):
    contract_id: str = ""
    party_type: str = ""
    party_id: str = ""


@dataclass(kw_only=True)
class TariffUpdatedEvent(BaseEvent):
    tariff_id: str = ""
    fee_type: str = ""
    rate: float = 0.0


@dataclass(kw_only=True)
class BudgetExceededEvent(BaseEvent):
    budget_id: str = ""
    cost_center: str = ""
    spent: float = 0.0
    amount: float = 0.0
