# Sprint 8.3 — CRM, marketplace and trading domain models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class LeadStatus(str, enum.Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class OfferStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    MATCHED = "matched"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class NegotiationStatus(str, enum.Enum):
    OPEN = "open"
    COUNTERED = "countered"
    AGREED = "agreed"
    CANCELLED = "cancelled"


class MarketplaceOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    CONFIRMED = "confirmed"
    IN_FULFILLMENT = "in_fulfillment"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ContractLifecycle(str, enum.Enum):
    DRAFT = "draft"
    PREPARED = "prepared"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DealStatus(str, enum.Enum):
    OPEN = "open"
    WON = "won"
    LOST = "lost"
    COMPLETED = "completed"


@dataclass
class FarmerProfile:
    profile_id: str = field(default_factory=_id)
    farmer_id: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    country: str = ""
    region: str = ""
    crops: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "farmer_id": self.farmer_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "country": self.country,
            "region": self.region,
            "crops": list(self.crops),
            "certifications": list(self.certifications),
            "score": self.score,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class BuyerProfile:
    profile_id: str = field(default_factory=_id)
    buyer_id: str = ""
    name: str = ""
    email: str = ""
    buyer_type: str = "processor"
    country: str = ""
    preferred_crops: list[str] = field(default_factory=list)
    budget_max: float = 0.0
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "buyer_id": self.buyer_id,
            "name": self.name,
            "email": self.email,
            "buyer_type": self.buyer_type,
            "country": self.country,
            "preferred_crops": list(self.preferred_crops),
            "budget_max": self.budget_max,
            "score": self.score,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class SupplierProfile:
    profile_id: str = field(default_factory=_id)
    supplier_id: str = ""
    name: str = ""
    email: str = ""
    category: str = "inputs"
    country: str = ""
    products: list[str] = field(default_factory=list)
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "supplier_id": self.supplier_id,
            "name": self.name,
            "email": self.email,
            "category": self.category,
            "country": self.country,
            "products": list(self.products),
            "score": self.score,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ExporterProfile:
    profile_id: str = field(default_factory=_id)
    exporter_id: str = ""
    name: str = ""
    email: str = ""
    country: str = ""
    destination_markets: list[str] = field(default_factory=list)
    licenses: list[str] = field(default_factory=list)
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "exporter_id": self.exporter_id,
            "name": self.name,
            "email": self.email,
            "country": self.country,
            "destination_markets": list(self.destination_markets),
            "licenses": list(self.licenses),
            "score": self.score,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class AgriculturalLead:
    lead_id: str = field(default_factory=_id)
    name: str = ""
    email: str = ""
    role: str = "buyer"
    source: str = "marketplace"
    status: LeadStatus = LeadStatus.NEW
    assignee_id: str = ""
    score: float = 0.0
    notes: str = ""
    crop_interest: str = ""
    region: str = ""
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "source": self.source,
            "status": self.status.value,
            "assignee_id": self.assignee_id,
            "score": self.score,
            "notes": self.notes,
            "crop_interest": self.crop_interest,
            "region": self.region,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class CRMContactEntry:
    entry_id: str = field(default_factory=_id)
    profile_id: str = ""
    profile_type: str = "buyer"
    channel: str = "email"
    subject: str = ""
    body: str = ""
    direction: str = "outbound"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "profile_id": self.profile_id,
            "profile_type": self.profile_type,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
            "direction": self.direction,
            "created_at": self.created_at,
        }


@dataclass
class CRMTask:
    task_id: str = field(default_factory=_id)
    title: str = ""
    related_id: str = ""
    related_type: str = "lead"
    assignee_id: str = ""
    status: str = "open"
    due_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "related_id": self.related_id,
            "related_type": self.related_type,
            "assignee_id": self.assignee_id,
            "status": self.status,
            "due_at": self.due_at,
            "created_at": self.created_at,
        }


@dataclass
class PurchaseRequest:
    request_id: str = field(default_factory=_id)
    buyer_id: str = ""
    crop_id: str = ""
    product_id: str = ""
    quantity: float = 0.0
    unit: str = "ton"
    max_price: float = 0.0
    currency: str = "USD"
    region: str = ""
    delivery_by: float = 0.0
    status: str = "open"
    notes: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "buyer_id": self.buyer_id,
            "crop_id": self.crop_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "max_price": self.max_price,
            "currency": self.currency,
            "region": self.region,
            "delivery_by": self.delivery_by,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class SalesOffer:
    offer_id: str = field(default_factory=_id)
    seller_id: str = ""
    seller_role: str = "farmer"
    product_id: str = ""
    crop_id: str = ""
    listing_id: str = ""
    quantity: float = 0.0
    unit: str = "ton"
    price: float = 0.0
    currency: str = "USD"
    region: str = ""
    status: OfferStatus = OfferStatus.DRAFT
    matched_request_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "seller_id": self.seller_id,
            "seller_role": self.seller_role,
            "product_id": self.product_id,
            "crop_id": self.crop_id,
            "listing_id": self.listing_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "price": self.price,
            "currency": self.currency,
            "region": self.region,
            "status": self.status.value,
            "matched_request_id": self.matched_request_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class PriceRequest:
    rfq_id: str = field(default_factory=_id)
    buyer_id: str = ""
    product_id: str = ""
    crop_id: str = ""
    quantity: float = 0.0
    target_price: float = 0.0
    currency: str = "USD"
    status: str = "open"
    responses: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rfq_id": self.rfq_id,
            "buyer_id": self.buyer_id,
            "product_id": self.product_id,
            "crop_id": self.crop_id,
            "quantity": self.quantity,
            "target_price": self.target_price,
            "currency": self.currency,
            "status": self.status,
            "responses": list(self.responses),
            "created_at": self.created_at,
        }


@dataclass
class Negotiation:
    negotiation_id: str = field(default_factory=_id)
    offer_id: str = ""
    request_id: str = ""
    buyer_id: str = ""
    seller_id: str = ""
    status: NegotiationStatus = NegotiationStatus.OPEN
    current_price: float = 0.0
    current_quantity: float = 0.0
    delivery_terms: str = ""
    rounds: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "negotiation_id": self.negotiation_id,
            "offer_id": self.offer_id,
            "request_id": self.request_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "status": self.status.value,
            "current_price": self.current_price,
            "current_quantity": self.current_quantity,
            "delivery_terms": self.delivery_terms,
            "rounds": list(self.rounds),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DeliveryAgreement:
    agreement_id: str = field(default_factory=_id)
    negotiation_id: str = ""
    order_id: str = ""
    origin: str = ""
    destination: str = ""
    delivery_by: float = 0.0
    carrier: str = ""
    terms: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agreement_id": self.agreement_id,
            "negotiation_id": self.negotiation_id,
            "order_id": self.order_id,
            "origin": self.origin,
            "destination": self.destination,
            "delivery_by": self.delivery_by,
            "carrier": self.carrier,
            "terms": dict(self.terms),
            "created_at": self.created_at,
        }


@dataclass
class MarketplaceOrder:
    order_id: str = field(default_factory=_id)
    buyer_id: str = ""
    seller_id: str = ""
    product_id: str = ""
    offer_id: str = ""
    negotiation_id: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    currency: str = "USD"
    status: MarketplaceOrderStatus = MarketplaceOrderStatus.DRAFT
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)
    confirmed_at: float = 0.0

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "product_id": self.product_id,
            "offer_id": self.offer_id,
            "negotiation_id": self.negotiation_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "currency": self.currency,
            "total": self.total,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "confirmed_at": self.confirmed_at,
        }


@dataclass
class TradeContract:
    contract_id: str = field(default_factory=_id)
    order_id: str = ""
    negotiation_id: str = ""
    parties: list[str] = field(default_factory=list)
    status: ContractLifecycle = ContractLifecycle.DRAFT
    terms: dict[str, Any] = field(default_factory=dict)
    prepared_at: float = 0.0
    signed_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "order_id": self.order_id,
            "negotiation_id": self.negotiation_id,
            "parties": list(self.parties),
            "status": self.status.value,
            "terms": dict(self.terms),
            "prepared_at": self.prepared_at,
            "signed_at": self.signed_at,
            "created_at": self.created_at,
        }


@dataclass
class TradingSession:
    session_id: str = field(default_factory=_id)
    buyer_id: str = ""
    seller_id: str = ""
    product_id: str = ""
    status: str = "active"
    offers: list[str] = field(default_factory=list)
    negotiations: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)
    closed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "product_id": self.product_id,
            "status": self.status,
            "offers": list(self.offers),
            "negotiations": list(self.negotiations),
            "created_at": self.created_at,
            "closed_at": self.closed_at,
        }


@dataclass
class MarketplaceDeal:
    deal_id: str = field(default_factory=_id)
    order_id: str = ""
    contract_id: str = ""
    buyer_id: str = ""
    seller_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: DealStatus = DealStatus.OPEN
    created_at: float = field(default_factory=_ts)
    completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "order_id": self.order_id,
            "contract_id": self.contract_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }
