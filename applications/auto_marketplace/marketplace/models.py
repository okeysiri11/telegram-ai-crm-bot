# Sprint 10.2 — marketplace, VIN, history, dealer network models.

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


class MarketplaceChannel(str, enum.Enum):
    PRIVATE_SELLER = "private_sellers"
    DEALER = "dealers"
    OFFICIAL_DEALER = "official_dealers"
    AUCTION = "auctions"
    WHOLESALE = "wholesale"
    RETAIL = "retail"
    COMMERCIAL = "commercial_vehicles"
    AGRICULTURAL = "agricultural_machinery"
    CONSTRUCTION = "construction_equipment"
    MOTORCYCLE = "motorcycles"
    ELECTRIC = "electric_vehicles"


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RESERVED = "reserved"
    SOLD = "sold"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    REVIEW = "review"


class DealerTier(str, enum.Enum):
    STANDARD = "standard"
    VERIFIED = "verified"
    OFFICIAL = "official"
    PREMIUM = "premium"


@dataclass
class MarketplaceListing:
    listing_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    seller_id: str = ""
    dealer_id: str = ""
    channel: MarketplaceChannel = MarketplaceChannel.RETAIL
    title: str = ""
    price: float = 0.0
    currency: str = "USD"
    region: str = ""
    status: ListingStatus = ListingStatus.DRAFT
    vin: str = ""
    media_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "vehicle_id": self.vehicle_id,
            "seller_id": self.seller_id,
            "dealer_id": self.dealer_id,
            "channel": self.channel.value,
            "title": self.title,
            "price": self.price,
            "currency": self.currency,
            "region": self.region,
            "status": self.status.value,
            "vin": self.vin,
            "media_ids": list(self.media_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class AuctionLot:
    auction_id: str = field(default_factory=_id)
    listing_id: str = ""
    start_price: float = 0.0
    current_bid: float = 0.0
    reserve_price: float = 0.0
    currency: str = "USD"
    ends_at: float = 0.0
    active: bool = True
    bids: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "auction_id": self.auction_id,
            "listing_id": self.listing_id,
            "start_price": self.start_price,
            "current_bid": self.current_bid,
            "reserve_price": self.reserve_price,
            "currency": self.currency,
            "ends_at": self.ends_at,
            "active": self.active,
            "bids": list(self.bids),
            "created_at": self.created_at,
        }


@dataclass
class VINDecodeResult:
    vin: str = ""
    valid: bool = False
    wmi: str = ""
    vds: str = ""
    vis: str = ""
    country: str = ""
    plant: str = ""
    manufacturer: str = ""
    production_year: int | None = None
    production_date: str = ""
    engine: str = ""
    transmission: str = ""
    body: str = ""
    drive: str = ""
    fuel: str = ""
    options: list[str] = field(default_factory=list)
    factory_configuration: dict[str, Any] = field(default_factory=dict)
    oem_specifications: dict[str, Any] = field(default_factory=dict)
    recalls: list[dict[str, Any]] = field(default_factory=list)
    service_campaigns: list[dict[str, Any]] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vin": self.vin,
            "valid": self.valid,
            "wmi": self.wmi,
            "vds": self.vds,
            "vis": self.vis,
            "country": self.country,
            "plant": self.plant,
            "manufacturer": self.manufacturer,
            "production_year": self.production_year,
            "production_date": self.production_date,
            "engine": self.engine,
            "transmission": self.transmission,
            "body": self.body,
            "drive": self.drive,
            "fuel": self.fuel,
            "options": list(self.options),
            "factory_configuration": dict(self.factory_configuration),
            "oem_specifications": dict(self.oem_specifications),
            "recalls": list(self.recalls),
            "service_campaigns": list(self.service_campaigns),
            "detail": self.detail,
        }


@dataclass
class VehicleHistoryRecord:
    record_id: str = field(default_factory=_id)
    vin: str = ""
    vehicle_id: str = ""
    ownership: list[dict[str, Any]] = field(default_factory=list)
    registrations: list[dict[str, Any]] = field(default_factory=list)
    mileage: list[dict[str, Any]] = field(default_factory=list)
    insurance_claims: list[dict[str, Any]] = field(default_factory=list)
    accidents: list[dict[str, Any]] = field(default_factory=list)
    repairs: list[dict[str, Any]] = field(default_factory=list)
    service_records: list[dict[str, Any]] = field(default_factory=list)
    import_export: list[dict[str, Any]] = field(default_factory=list)
    theft_status: str = "clear"
    lien_status: str = "clear"
    inspections: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "vin": self.vin,
            "vehicle_id": self.vehicle_id,
            "ownership": list(self.ownership),
            "registrations": list(self.registrations),
            "mileage": list(self.mileage),
            "insurance_claims": list(self.insurance_claims),
            "accidents": list(self.accidents),
            "repairs": list(self.repairs),
            "service_records": list(self.service_records),
            "import_export": list(self.import_export),
            "theft_status": self.theft_status,
            "lien_status": self.lien_status,
            "inspections": list(self.inspections),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DealerNetworkProfile:
    profile_id: str = field(default_factory=_id)
    dealer_id: str = ""
    name: str = ""
    tier: DealerTier = DealerTier.STANDARD
    verified: bool = False
    rating: float = 0.0
    review_count: int = 0
    region: str = ""
    branches: list[dict[str, Any]] = field(default_factory=list)
    managers: list[dict[str, Any]] = field(default_factory=list)
    inventory_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "dealer_id": self.dealer_id,
            "name": self.name,
            "tier": self.tier.value,
            "verified": self.verified,
            "rating": self.rating,
            "review_count": self.review_count,
            "region": self.region,
            "branches": list(self.branches),
            "managers": list(self.managers),
            "inventory_count": self.inventory_count,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class VerificationReport:
    report_id: str = field(default_factory=_id)
    listing_id: str = ""
    vehicle_id: str = ""
    vin: str = ""
    photo_status: VerificationStatus = VerificationStatus.PENDING
    vin_status: VerificationStatus = VerificationStatus.PENDING
    duplicate_score: float = 0.0
    fraud_score: float = 0.0
    ai_image_score: float = 0.0
    damage_estimate: float = 0.0
    status: VerificationStatus = VerificationStatus.PENDING
    findings: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "listing_id": self.listing_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "photo_status": self.photo_status.value,
            "vin_status": self.vin_status.value,
            "duplicate_score": self.duplicate_score,
            "fraud_score": self.fraud_score,
            "ai_image_score": self.ai_image_score,
            "damage_estimate": self.damage_estimate,
            "status": self.status.value,
            "findings": list(self.findings),
            "created_at": self.created_at,
        }


@dataclass
class MarketValuation:
    valuation_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    vin: str = ""
    average_price: float = 0.0
    dealer_price: float = 0.0
    wholesale_price: float = 0.0
    retail_price: float = 0.0
    ai_valuation: float = 0.0
    currency: str = "USD"
    confidence: float = 0.7
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valuation_id": self.valuation_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "average_price": self.average_price,
            "dealer_price": self.dealer_price,
            "wholesale_price": self.wholesale_price,
            "retail_price": self.retail_price,
            "ai_valuation": self.ai_valuation,
            "currency": self.currency,
            "confidence": self.confidence,
            "history": list(self.history),
            "created_at": self.created_at,
        }


@dataclass
class OwnershipTransfer:
    transfer_id: str = field(default_factory=_id)
    vin: str = ""
    from_owner: str = ""
    to_owner: str = ""
    transferred_at: float = field(default_factory=_ts)
    region: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "vin": self.vin,
            "from_owner": self.from_owner,
            "to_owner": self.to_owner,
            "transferred_at": self.transferred_at,
            "region": self.region,
            "notes": self.notes,
        }
