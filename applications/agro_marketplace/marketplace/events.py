# Sprint 8.3 — CRM and trading events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class FarmerRegisteredTradingEvent(BaseEvent):
    farmer_id: str = ""
    profile_id: str = ""
    email: str = ""
    name: str = ""


@dataclass(kw_only=True)
class BuyerRegisteredEvent(BaseEvent):
    buyer_id: str = ""
    profile_id: str = ""
    email: str = ""
    name: str = ""


@dataclass(kw_only=True)
class OfferPublishedEvent(BaseEvent):
    offer_id: str = ""
    seller_id: str = ""
    product_id: str = ""
    price: float = 0.0
    quantity: float = 0.0


@dataclass(kw_only=True)
class OfferMatchedEvent(BaseEvent):
    offer_id: str = ""
    request_id: str = ""
    score: float = 0.0


@dataclass(kw_only=True)
class NegotiationStartedEvent(BaseEvent):
    negotiation_id: str = ""
    offer_id: str = ""
    buyer_id: str = ""
    seller_id: str = ""


@dataclass(kw_only=True)
class ContractPreparedEvent(BaseEvent):
    contract_id: str = ""
    order_id: str = ""
    negotiation_id: str = ""


@dataclass(kw_only=True)
class OrderConfirmedEvent(BaseEvent):
    order_id: str = ""
    buyer_id: str = ""
    seller_id: str = ""
    total: float = 0.0


@dataclass(kw_only=True)
class TradeCompletedEvent(BaseEvent):
    deal_id: str = ""
    order_id: str = ""
    amount: float = 0.0
