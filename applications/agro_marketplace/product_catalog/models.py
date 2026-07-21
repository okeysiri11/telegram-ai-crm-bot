# Sprint 8.2 — agricultural catalog / warehouse / inventory domain models.

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


class AvailabilityStatus(str, enum.Enum):
    DRAFT = "draft"
    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_TRANSIT = "in_transit"
    SOLD_OUT = "sold_out"
    ARCHIVED = "archived"


class UnitOfMeasure(str, enum.Enum):
    KG = "kg"
    TON = "ton"
    LITER = "liter"
    BUSHEL = "bushel"
    BAG = "bag"
    PIECE = "piece"


class MovementType(str, enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"


class QualityGrade(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    REJECT = "reject"


@dataclass
class Season:
    season_id: str = field(default_factory=_id)
    name: str = ""
    year: int = 0
    start_date: float = 0.0
    end_date: float = 0.0
    region: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "season_id": self.season_id,
            "name": self.name,
            "year": self.year,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "region": self.region,
            "created_at": self.created_at,
        }


@dataclass
class Crop:
    crop_id: str = field(default_factory=_id)
    name: str = ""
    scientific_name: str = ""
    category: str = ""
    typical_uom: UnitOfMeasure = UnitOfMeasure.TON
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "crop_id": self.crop_id,
            "name": self.name,
            "scientific_name": self.scientific_name,
            "category": self.category,
            "typical_uom": self.typical_uom.value,
            "created_at": self.created_at,
        }


@dataclass
class CropVariety:
    variety_id: str = field(default_factory=_id)
    crop_id: str = ""
    name: str = ""
    traits: list[str] = field(default_factory=list)
    maturity_days: int = 0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "variety_id": self.variety_id,
            "crop_id": self.crop_id,
            "name": self.name,
            "traits": list(self.traits),
            "maturity_days": self.maturity_days,
            "created_at": self.created_at,
        }


@dataclass
class Packaging:
    packaging_id: str = field(default_factory=_id)
    name: str = ""
    material: str = ""
    capacity: float = 0.0
    uom: UnitOfMeasure = UnitOfMeasure.KG
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "packaging_id": self.packaging_id,
            "name": self.name,
            "material": self.material,
            "capacity": self.capacity,
            "uom": self.uom.value,
            "created_at": self.created_at,
        }


@dataclass
class AgriculturalProduct:
    product_id: str = field(default_factory=_id)
    name: str = ""
    sku: str = ""
    category_id: str = ""
    crop_id: str = ""
    variety_id: str = ""
    farmer_id: str = ""
    supplier_id: str = ""
    region: str = ""
    description: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    uom: UnitOfMeasure = UnitOfMeasure.TON
    quantity: float = 0.0
    price: float = 0.0
    currency: str = "USD"
    packaging_id: str = ""
    status: AvailabilityStatus = AvailabilityStatus.DRAFT
    quality_score: float = 0.0
    duplicate_of: str = ""
    season_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "sku": self.sku,
            "category_id": self.category_id,
            "crop_id": self.crop_id,
            "variety_id": self.variety_id,
            "farmer_id": self.farmer_id,
            "supplier_id": self.supplier_id,
            "region": self.region,
            "description": self.description,
            "attributes": dict(self.attributes),
            "tags": list(self.tags),
            "uom": self.uom.value,
            "quantity": self.quantity,
            "price": self.price,
            "currency": self.currency,
            "packaging_id": self.packaging_id,
            "status": self.status.value,
            "quality_score": self.quality_score,
            "duplicate_of": self.duplicate_of,
            "season_id": self.season_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class HarvestRecord:
    """Enterprise harvest registration (Sprint 8.2)."""

    harvest_id: str = field(default_factory=_id)
    farm_id: str = ""
    field_id: str = ""
    crop_id: str = ""
    variety_id: str = ""
    season_id: str = ""
    farmer_id: str = ""
    region: str = ""
    quantity: float = 0.0
    uom: UnitOfMeasure = UnitOfMeasure.TON
    yield_per_hectare: float = 0.0
    quality_grade: QualityGrade = QualityGrade.A
    moisture_pct: float = 0.0
    protein_pct: float = 0.0
    foreign_material_pct: float = 0.0
    harvest_date: float = field(default_factory=_ts)
    notes: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "harvest_id": self.harvest_id,
            "farm_id": self.farm_id,
            "field_id": self.field_id,
            "crop_id": self.crop_id,
            "variety_id": self.variety_id,
            "season_id": self.season_id,
            "farmer_id": self.farmer_id,
            "region": self.region,
            "quantity": self.quantity,
            "uom": self.uom.value,
            "yield_per_hectare": self.yield_per_hectare,
            "quality_grade": self.quality_grade.value,
            "moisture_pct": self.moisture_pct,
            "protein_pct": self.protein_pct,
            "foreign_material_pct": self.foreign_material_pct,
            "harvest_date": self.harvest_date,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class HarvestBatch:
    batch_id: str = field(default_factory=_id)
    harvest_id: str = ""
    batch_code: str = ""
    quantity: float = 0.0
    uom: UnitOfMeasure = UnitOfMeasure.TON
    quality_grade: QualityGrade = QualityGrade.A
    warehouse_id: str = ""
    location_id: str = ""
    lot_id: str = ""
    status: str = "open"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "harvest_id": self.harvest_id,
            "batch_code": self.batch_code,
            "quantity": self.quantity,
            "uom": self.uom.value,
            "quality_grade": self.quality_grade.value,
            "warehouse_id": self.warehouse_id,
            "location_id": self.location_id,
            "lot_id": self.lot_id,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class AgroWarehouse:
    warehouse_id: str = field(default_factory=_id)
    name: str = ""
    owner_id: str = ""
    region: str = ""
    location: str = ""
    capacity_tons: float = 0.0
    used_tons: float = 0.0
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    @property
    def available_tons(self) -> float:
        return max(0.0, self.capacity_tons - self.used_tons)

    def to_dict(self) -> dict[str, Any]:
        return {
            "warehouse_id": self.warehouse_id,
            "name": self.name,
            "owner_id": self.owner_id,
            "region": self.region,
            "location": self.location,
            "capacity_tons": self.capacity_tons,
            "used_tons": self.used_tons,
            "available_tons": self.available_tons,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class StorageLocation:
    location_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    code: str = ""
    zone: str = ""
    capacity_tons: float = 0.0
    used_tons: float = 0.0
    temperature_c: float | None = None
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "location_id": self.location_id,
            "warehouse_id": self.warehouse_id,
            "code": self.code,
            "zone": self.zone,
            "capacity_tons": self.capacity_tons,
            "used_tons": self.used_tons,
            "temperature_c": self.temperature_c,
            "created_at": self.created_at,
        }


@dataclass
class StorageLotRecord:
    lot_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    location_id: str = ""
    product_id: str = ""
    batch_id: str = ""
    harvest_id: str = ""
    quantity_tons: float = 0.0
    quality_grade: QualityGrade = QualityGrade.A
    status: str = "stored"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lot_id": self.lot_id,
            "warehouse_id": self.warehouse_id,
            "location_id": self.location_id,
            "product_id": self.product_id,
            "batch_id": self.batch_id,
            "harvest_id": self.harvest_id,
            "quantity_tons": self.quantity_tons,
            "quality_grade": self.quality_grade.value,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class InventoryItem:
    item_id: str = field(default_factory=_id)
    product_id: str = ""
    warehouse_id: str = ""
    location_id: str = ""
    lot_id: str = ""
    batch_id: str = ""
    quantity: float = 0.0
    reserved_quantity: float = 0.0
    uom: UnitOfMeasure = UnitOfMeasure.TON
    status: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    updated_at: float = field(default_factory=_ts)
    created_at: float = field(default_factory=_ts)

    @property
    def available_quantity(self) -> float:
        return max(0.0, self.quantity - self.reserved_quantity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "product_id": self.product_id,
            "warehouse_id": self.warehouse_id,
            "location_id": self.location_id,
            "lot_id": self.lot_id,
            "batch_id": self.batch_id,
            "quantity": self.quantity,
            "reserved_quantity": self.reserved_quantity,
            "available_quantity": self.available_quantity,
            "uom": self.uom.value,
            "status": self.status.value,
            "updated_at": self.updated_at,
            "created_at": self.created_at,
        }


@dataclass
class InventoryMovement:
    movement_id: str = field(default_factory=_id)
    movement_type: MovementType = MovementType.INCOMING
    product_id: str = ""
    quantity: float = 0.0
    uom: UnitOfMeasure = UnitOfMeasure.TON
    from_warehouse_id: str = ""
    to_warehouse_id: str = ""
    from_location_id: str = ""
    to_location_id: str = ""
    lot_id: str = ""
    batch_id: str = ""
    reference: str = ""
    notes: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "movement_id": self.movement_id,
            "movement_type": self.movement_type.value,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "uom": self.uom.value,
            "from_warehouse_id": self.from_warehouse_id,
            "to_warehouse_id": self.to_warehouse_id,
            "from_location_id": self.from_location_id,
            "to_location_id": self.to_location_id,
            "lot_id": self.lot_id,
            "batch_id": self.batch_id,
            "reference": self.reference,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class QualityCertificateRecord:
    certificate_id: str = field(default_factory=_id)
    product_id: str = ""
    harvest_id: str = ""
    batch_id: str = ""
    issuer: str = ""
    grade: QualityGrade = QualityGrade.A
    verified: bool = False
    issued_at: float = field(default_factory=_ts)
    expires_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "product_id": self.product_id,
            "harvest_id": self.harvest_id,
            "batch_id": self.batch_id,
            "issuer": self.issuer,
            "grade": self.grade.value,
            "verified": self.verified,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }


@dataclass
class LaboratoryResult:
    result_id: str = field(default_factory=_id)
    harvest_id: str = ""
    batch_id: str = ""
    lab_name: str = ""
    moisture_pct: float = 0.0
    protein_pct: float = 0.0
    foreign_material_pct: float = 0.0
    toxins_ppm: float = 0.0
    grade: QualityGrade = QualityGrade.A
    notes: str = ""
    tested_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "harvest_id": self.harvest_id,
            "batch_id": self.batch_id,
            "lab_name": self.lab_name,
            "moisture_pct": self.moisture_pct,
            "protein_pct": self.protein_pct,
            "foreign_material_pct": self.foreign_material_pct,
            "toxins_ppm": self.toxins_ppm,
            "grade": self.grade.value,
            "notes": self.notes,
            "tested_at": self.tested_at,
        }


# Aliases matching requirement naming
Harvest = HarvestRecord
Warehouse = AgroWarehouse
StorageLot = StorageLotRecord
QualityCertificate = QualityCertificateRecord
