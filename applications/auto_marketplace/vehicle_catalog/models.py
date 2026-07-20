# Catalog vehicle aggregate model.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from applications.auto_marketplace.specifications.models import (
    DriveType,
    FuelType,
    InventoryVehicleStatus,
    Transmission,
    VehicleColor,
    VehicleCondition,
    VehicleEngine,
    VehicleFeature,
    VehicleLocation,
    VehicleOption,
)


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


@dataclass
class CatalogVehicle:
    vehicle_id: str = field(default_factory=_id)
    vin: str = ""
    dealer_id: str = ""
    brand: str = ""
    model: str = ""
    generation: str = ""
    trim: str = ""
    year: int = 0
    mileage_km: int = 0
    price: float = 0.0
    currency: str = "USD"
    condition: VehicleCondition = VehicleCondition.USED
    status: InventoryVehicleStatus = InventoryVehicleStatus.DRAFT
    engine: VehicleEngine = field(default_factory=VehicleEngine)
    transmission: Transmission = Transmission.AUTOMATIC
    drive_type: DriveType = DriveType.FWD
    fuel_type: FuelType = FuelType.GASOLINE
    color_exterior: VehicleColor = field(default_factory=VehicleColor)
    color_interior: VehicleColor = field(default_factory=lambda: VehicleColor(type="interior"))
    location: VehicleLocation = field(default_factory=VehicleLocation)
    features: list[VehicleFeature] = field(default_factory=list)
    options: list[VehicleOption] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    media_ids: list[str] = field(default_factory=list)
    quality_score: float = 0.0
    category: str = ""
    description: str = ""
    duplicate_of: str | None = None
    warehouse_id: str = ""
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)
    archived_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "dealer_id": self.dealer_id,
            "brand": self.brand,
            "model": self.model,
            "generation": self.generation,
            "trim": self.trim,
            "year": self.year,
            "mileage_km": self.mileage_km,
            "price": self.price,
            "currency": self.currency,
            "condition": self.condition.value,
            "status": self.status.value,
            "engine": self.engine.to_dict(),
            "transmission": self.transmission.value,
            "drive_type": self.drive_type.value,
            "fuel_type": self.fuel_type.value,
            "color_exterior": self.color_exterior.to_dict(),
            "color_interior": self.color_interior.to_dict(),
            "location": self.location.to_dict(),
            "features": [f.to_dict() for f in self.features],
            "options": [o.to_dict() for o in self.options],
            "tags": list(self.tags),
            "media_ids": list(self.media_ids),
            "quality_score": self.quality_score,
            "category": self.category,
            "description": self.description,
            "duplicate_of": self.duplicate_of,
            "warehouse_id": self.warehouse_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "archived_at": self.archived_at,
        }
