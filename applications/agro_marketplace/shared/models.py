# Agro Marketplace — domain models (Sprint 8.1).

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


class AgroRole(str, enum.Enum):
    FARMER = "farmer"
    BUYER = "buyer"
    SUPPLIER = "supplier"
    EXPORTER = "exporter"
    LOGISTICS = "logistics"
    ADMINISTRATOR = "administrator"
    OWNER = "owner"
    AI_AGENT = "ai_agent"


class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    LISTED = "listed"
    RESERVED = "reserved"
    SOLD = "sold"
    ARCHIVED = "archived"


class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PLACED = "placed"
    CONFIRMED = "confirmed"
    IN_FULFILLMENT = "in_fulfillment"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ExportStatus(str, enum.Enum):
    DRAFT = "draft"
    STARTED = "started"
    CLEARED = "cleared"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    CANCELLED = "cancelled"


@dataclass
class Farmer:
    farmer_id: str = field(default_factory=_id)
    name: str = ""
    email: str = ""
    phone: str = ""
    country: str = ""
    region: str = ""
    certifications: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "farmer_id": self.farmer_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "country": self.country,
            "region": self.region,
            "certifications": list(self.certifications),
            "created_at": self.created_at,
        }


@dataclass
class Farm:
    farm_id: str = field(default_factory=_id)
    farmer_id: str = ""
    name: str = ""
    location: str = ""
    size_hectares: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "farm_id": self.farm_id,
            "farmer_id": self.farmer_id,
            "name": self.name,
            "location": self.location,
            "size_hectares": self.size_hectares,
            "created_at": self.created_at,
        }


@dataclass
class Field:
    field_id: str = field(default_factory=_id)
    farm_id: str = ""
    name: str = ""
    crop_type: str = ""
    area_hectares: float = 0.0
    soil_type: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "farm_id": self.farm_id,
            "name": self.name,
            "crop_type": self.crop_type,
            "area_hectares": self.area_hectares,
            "soil_type": self.soil_type,
            "created_at": self.created_at,
        }


@dataclass
class Warehouse:
    warehouse_id: str = field(default_factory=_id)
    name: str = ""
    owner_id: str = ""
    location: str = ""
    capacity_tons: float = 0.0
    used_tons: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "warehouse_id": self.warehouse_id,
            "name": self.name,
            "owner_id": self.owner_id,
            "location": self.location,
            "capacity_tons": self.capacity_tons,
            "used_tons": self.used_tons,
            "created_at": self.created_at,
        }


@dataclass
class Supplier:
    supplier_id: str = field(default_factory=_id)
    name: str = ""
    email: str = ""
    category: str = "inputs"
    country: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "email": self.email,
            "category": self.category,
            "country": self.country,
            "created_at": self.created_at,
        }


@dataclass
class Buyer:
    buyer_id: str = field(default_factory=_id)
    name: str = ""
    email: str = ""
    buyer_type: str = "processor"
    country: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "buyer_id": self.buyer_id,
            "name": self.name,
            "email": self.email,
            "buyer_type": self.buyer_type,
            "country": self.country,
            "created_at": self.created_at,
        }


@dataclass
class ProductCategory:
    category_id: str = field(default_factory=_id)
    name: str = ""
    parent_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category_id": self.category_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
        }


@dataclass
class Crop:
    crop_id: str = field(default_factory=_id)
    name: str = ""
    scientific_name: str = ""
    season: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "crop_id": self.crop_id,
            "name": self.name,
            "scientific_name": self.scientific_name,
            "season": self.season,
            "created_at": self.created_at,
        }


@dataclass
class Harvest:
    harvest_id: str = field(default_factory=_id)
    farm_id: str = ""
    field_id: str = ""
    crop_id: str = ""
    quantity_tons: float = 0.0
    harvest_date: float = field(default_factory=_ts)
    quality_grade: str = "A"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "harvest_id": self.harvest_id,
            "farm_id": self.farm_id,
            "field_id": self.field_id,
            "crop_id": self.crop_id,
            "quantity_tons": self.quantity_tons,
            "harvest_date": self.harvest_date,
            "quality_grade": self.quality_grade,
            "created_at": self.created_at,
        }


@dataclass
class Product:
    product_id: str = field(default_factory=_id)
    name: str = ""
    category_id: str = ""
    crop_id: str = ""
    farmer_id: str = ""
    unit: str = "ton"
    quantity: float = 0.0
    price: float = 0.0
    currency: str = "USD"
    status: ProductStatus = ProductStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "category_id": self.category_id,
            "crop_id": self.crop_id,
            "farmer_id": self.farmer_id,
            "unit": self.unit,
            "quantity": self.quantity,
            "price": self.price,
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class MarketplaceListing:
    listing_id: str = field(default_factory=_id)
    product_id: str = ""
    title: str = ""
    description: str = ""
    is_active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "product_id": self.product_id,
            "title": self.title,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class Offer:
    offer_id: str = field(default_factory=_id)
    product_id: str = ""
    buyer_id: str = ""
    price: float = 0.0
    quantity: float = 0.0
    status: str = "pending"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "product_id": self.product_id,
            "buyer_id": self.buyer_id,
            "price": self.price,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class Order:
    order_id: str = field(default_factory=_id)
    buyer_id: str = ""
    farmer_id: str = ""
    product_id: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    currency: str = "USD"
    status: OrderStatus = OrderStatus.DRAFT
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "buyer_id": self.buyer_id,
            "farmer_id": self.farmer_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "currency": self.currency,
            "total": self.total,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Contract:
    contract_id: str = field(default_factory=_id)
    order_id: str = ""
    parties: list[str] = field(default_factory=list)
    status: ContractStatus = ContractStatus.DRAFT
    terms: dict[str, Any] = field(default_factory=dict)
    signed_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "order_id": self.order_id,
            "parties": list(self.parties),
            "status": self.status.value,
            "terms": dict(self.terms),
            "signed_at": self.signed_at,
            "created_at": self.created_at,
        }


@dataclass
class Delivery:
    delivery_id: str = field(default_factory=_id)
    order_id: str = ""
    carrier: str = ""
    origin: str = ""
    destination: str = ""
    status: DeliveryStatus = DeliveryStatus.SCHEDULED
    created_at: float = field(default_factory=_ts)
    completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "order_id": self.order_id,
            "carrier": self.carrier,
            "origin": self.origin,
            "destination": self.destination,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class ExportShipment:
    shipment_id: str = field(default_factory=_id)
    order_id: str = ""
    exporter_id: str = ""
    destination_country: str = ""
    status: ExportStatus = ExportStatus.DRAFT
    documents: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shipment_id": self.shipment_id,
            "order_id": self.order_id,
            "exporter_id": self.exporter_id,
            "destination_country": self.destination_country,
            "status": self.status.value,
            "documents": list(self.documents),
            "created_at": self.created_at,
        }


@dataclass
class QualityCertificate:
    certificate_id: str = field(default_factory=_id)
    product_id: str = ""
    harvest_id: str = ""
    issuer: str = ""
    grade: str = "A"
    issued_at: float = field(default_factory=_ts)
    expires_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "product_id": self.product_id,
            "harvest_id": self.harvest_id,
            "issuer": self.issuer,
            "grade": self.grade,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }


@dataclass
class StorageLot:
    lot_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    product_id: str = ""
    quantity_tons: float = 0.0
    quality_grade: str = "A"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lot_id": self.lot_id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "quantity_tons": self.quantity_tons,
            "quality_grade": self.quality_grade,
            "created_at": self.created_at,
        }
