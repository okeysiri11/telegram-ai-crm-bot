# Auto Marketplace — domain models.

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


class VehicleStatus(str, enum.Enum):
    DRAFT = "draft"
    LISTED = "listed"
    RESERVED = "reserved"
    SOLD = "sold"
    ARCHIVED = "archived"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class DealStatus(str, enum.Enum):
    OPEN = "open"
    NEGOTIATING = "negotiating"
    PENDING_PAYMENT = "pending_payment"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class DeliveryStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class VehicleSpecification:
    make: str
    model: str
    year: int
    trim: str = ""
    engine: str = ""
    transmission: str = ""
    drivetrain: str = ""
    fuel_type: str = ""
    mileage_km: int = 0
    color_exterior: str = ""
    color_interior: str = ""
    body_type: str = ""
    vin: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class VehiclePhoto:
    photo_id: str = field(default_factory=_id)
    url: str = ""
    caption: str = ""
    sort_order: int = 0
    is_primary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "photo_id": self.photo_id,
            "url": self.url,
            "caption": self.caption,
            "sort_order": self.sort_order,
            "is_primary": self.is_primary,
        }


@dataclass
class VehicleVideo:
    video_id: str = field(default_factory=_id)
    url: str = ""
    caption: str = ""
    duration_sec: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "url": self.url,
            "caption": self.caption,
            "duration_sec": self.duration_sec,
        }


@dataclass
class Vehicle:
    vehicle_id: str = field(default_factory=_id)
    dealer_id: str = ""
    specification: VehicleSpecification = field(default_factory=lambda: VehicleSpecification("", "", 0))
    status: VehicleStatus = VehicleStatus.DRAFT
    price: float = 0.0
    currency: str = "USD"
    photos: list[VehiclePhoto] = field(default_factory=list)
    videos: list[VehicleVideo] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    description: str = ""
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vehicle_id": self.vehicle_id,
            "dealer_id": self.dealer_id,
            "specification": self.specification.to_dict(),
            "status": self.status.value,
            "price": self.price,
            "currency": self.currency,
            "photos": [p.to_dict() for p in self.photos],
            "videos": [v.to_dict() for v in self.videos],
            "features": list(self.features),
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DealerBranch:
    branch_id: str = field(default_factory=_id)
    name: str = ""
    address: str = ""
    city: str = ""
    country: str = ""
    phone: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Dealer:
    dealer_id: str = field(default_factory=_id)
    name: str = ""
    legal_name: str = ""
    email: str = ""
    phone: str = ""
    rating: float = 0.0
    branches: list[DealerBranch] = field(default_factory=list)
    verified: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dealer_id": self.dealer_id,
            "name": self.name,
            "legal_name": self.legal_name,
            "email": self.email,
            "phone": self.phone,
            "rating": self.rating,
            "branches": [b.to_dict() for b in self.branches],
            "verified": self.verified,
            "created_at": self.created_at,
        }


@dataclass
class Customer:
    customer_id: str = field(default_factory=_id)
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    preferences: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "preferences": dict(self.preferences),
            "created_at": self.created_at,
        }


@dataclass
class Lead:
    lead_id: str = field(default_factory=_id)
    customer_id: str = ""
    vehicle_id: str = ""
    dealer_id: str = ""
    source: str = "web"
    status: LeadStatus = LeadStatus.NEW
    notes: str = ""
    score: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "customer_id": self.customer_id,
            "vehicle_id": self.vehicle_id,
            "dealer_id": self.dealer_id,
            "source": self.source,
            "status": self.status.value,
            "notes": self.notes,
            "score": self.score,
            "created_at": self.created_at,
        }


@dataclass
class Offer:
    offer_id: str = field(default_factory=_id)
    deal_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    expires_at: float | None = None
    accepted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "deal_id": self.deal_id,
            "amount": self.amount,
            "currency": self.currency,
            "expires_at": self.expires_at,
            "accepted": self.accepted,
        }


@dataclass
class Deal:
    deal_id: str = field(default_factory=_id)
    customer_id: str = ""
    dealer_id: str = ""
    vehicle_id: str = ""
    status: DealStatus = DealStatus.OPEN
    offers: list[Offer] = field(default_factory=list)
    final_price: float | None = None
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "customer_id": self.customer_id,
            "dealer_id": self.dealer_id,
            "vehicle_id": self.vehicle_id,
            "status": self.status.value,
            "offers": [o.to_dict() for o in self.offers],
            "final_price": self.final_price,
            "created_at": self.created_at,
        }


@dataclass
class Reservation:
    reservation_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    customer_id: str = ""
    dealer_id: str = ""
    expires_at: float = field(default_factory=lambda: _ts() + 86400)
    deposit_amount: float = 0.0
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Inspection:
    inspection_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    inspector: str = ""
    score: float = 0.0
    report_url: str = ""
    findings: list[str] = field(default_factory=list)
    inspected_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "inspection_id": self.inspection_id,
            "vehicle_id": self.vehicle_id,
            "inspector": self.inspector,
            "score": self.score,
            "report_url": self.report_url,
            "findings": list(self.findings),
            "inspected_at": self.inspected_at,
        }


@dataclass
class TradeIn:
    trade_in_id: str = field(default_factory=_id)
    customer_id: str = ""
    deal_id: str = ""
    specification: VehicleSpecification = field(default_factory=lambda: VehicleSpecification("", "", 0))
    estimated_value: float = 0.0
    accepted_value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_in_id": self.trade_in_id,
            "customer_id": self.customer_id,
            "deal_id": self.deal_id,
            "specification": self.specification.to_dict(),
            "estimated_value": self.estimated_value,
            "accepted_value": self.accepted_value,
        }


@dataclass
class Auction:
    auction_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    dealer_id: str = ""
    start_price: float = 0.0
    current_bid: float = 0.0
    ends_at: float = field(default_factory=lambda: _ts() + 604800)
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Payment:
    payment_id: str = field(default_factory=_id)
    deal_id: str = ""
    customer_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    provider: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "deal_id": self.deal_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "provider": self.provider,
            "created_at": self.created_at,
        }


@dataclass
class Invoice:
    invoice_id: str = field(default_factory=_id)
    deal_id: str = ""
    payment_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    issued_at: float = field(default_factory=_ts)
    pdf_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Delivery:
    delivery_id: str = field(default_factory=_id)
    deal_id: str = ""
    customer_id: str = ""
    address: str = ""
    status: DeliveryStatus = DeliveryStatus.SCHEDULED
    scheduled_at: float | None = None
    delivered_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "deal_id": self.deal_id,
            "customer_id": self.customer_id,
            "address": self.address,
            "status": self.status.value,
            "scheduled_at": self.scheduled_at,
            "delivered_at": self.delivered_at,
        }


@dataclass
class ServiceHistory:
    record_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    service_type: str = ""
    description: str = ""
    mileage_km: int = 0
    performed_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Warranty:
    warranty_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    provider: str = ""
    coverage: str = ""
    starts_at: float = field(default_factory=_ts)
    ends_at: float = field(default_factory=lambda: _ts() + 31536000)

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}
