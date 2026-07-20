# Vehicle specification domain models — Sprint 6.2.

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


class Transmission(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CVT = "cvt"
    DCT = "dct"
    OTHER = "other"


class DriveType(str, enum.Enum):
    FWD = "fwd"
    RWD = "rwd"
    AWD = "awd"
    FOUR_WD = "4wd"


class FuelType(str, enum.Enum):
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    PLUGIN_HYBRID = "plugin_hybrid"
    ELECTRIC = "electric"
    HYDROGEN = "hydrogen"
    OTHER = "other"


class VehicleCondition(str, enum.Enum):
    NEW = "new"
    USED = "used"
    CERTIFIED = "certified"
    DAMAGED = "damaged"
    SALVAGE = "salvage"


class InventoryVehicleStatus(str, enum.Enum):
    DRAFT = "draft"
    INCOMING = "incoming"
    AVAILABLE = "available"
    LISTED = "listed"
    RESERVED = "reserved"
    SOLD = "sold"
    OUTGOING = "outgoing"
    ARCHIVED = "archived"


@dataclass
class VehicleBrand:
    brand_id: str = field(default_factory=_id)
    name: str = ""
    country: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"brand_id": self.brand_id, "name": self.name, "country": self.country}


@dataclass
class VehicleModel:
    model_id: str = field(default_factory=_id)
    brand_id: str = ""
    name: str = ""
    body_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"model_id": self.model_id, "brand_id": self.brand_id, "name": self.name, "body_type": self.body_type}


@dataclass
class VehicleGeneration:
    generation_id: str = field(default_factory=_id)
    model_id: str = ""
    name: str = ""
    year_from: int = 0
    year_to: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "model_id": self.model_id,
            "name": self.name,
            "year_from": self.year_from,
            "year_to": self.year_to,
        }


@dataclass
class VehicleTrim:
    trim_id: str = field(default_factory=_id)
    generation_id: str = ""
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"trim_id": self.trim_id, "generation_id": self.generation_id, "name": self.name}


@dataclass
class VehicleEngine:
    engine_id: str = field(default_factory=_id)
    displacement_l: float = 0.0
    cylinders: int = 0
    horsepower: int = 0
    torque_nm: int = 0
    fuel_type: FuelType = FuelType.GASOLINE

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "displacement_l": self.displacement_l,
            "cylinders": self.cylinders,
            "horsepower": self.horsepower,
            "torque_nm": self.torque_nm,
            "fuel_type": self.fuel_type.value,
        }


@dataclass
class VehicleColor:
    color_id: str = field(default_factory=_id)
    name: str = ""
    hex_code: str = ""
    type: str = "exterior"

    def to_dict(self) -> dict[str, Any]:
        return {"color_id": self.color_id, "name": self.name, "hex_code": self.hex_code, "type": self.type}


@dataclass
class VehicleLocation:
    location_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    dealer_id: str = ""
    address: str = ""
    city: str = ""
    country: str = ""
    latitude: float | None = None
    longitude: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "location_id": self.location_id,
            "warehouse_id": self.warehouse_id,
            "dealer_id": self.dealer_id,
            "address": self.address,
            "city": self.city,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


@dataclass
class VehicleFeature:
    feature_id: str = field(default_factory=_id)
    name: str = ""
    category: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"feature_id": self.feature_id, "name": self.name, "category": self.category}


@dataclass
class VehicleOption:
    option_id: str = field(default_factory=_id)
    name: str = ""
    price: float = 0.0
    installed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "option_id": self.option_id,
            "name": self.name,
            "price": self.price,
            "installed": self.installed,
        }
