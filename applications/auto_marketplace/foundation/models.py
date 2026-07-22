# Sprint 10.1 — Auto Marketplace foundation domain models.

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


class CatalogCategory(str, enum.Enum):
    CARS = "cars"
    MOTORCYCLES = "motorcycles"
    COMMERCIAL = "commercial_vehicles"
    AGRICULTURAL = "agricultural_machinery"
    CONSTRUCTION = "construction_machinery"
    ELECTRIC = "electric_vehicles"
    HYBRID = "hybrid_vehicles"
    PARTS = "parts"
    ACCESSORIES = "accessories"


class FuelType(str, enum.Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    PLUGIN_HYBRID = "plugin_hybrid"
    LPG = "lpg"
    CNG = "cng"
    HYDROGEN = "hydrogen"


class TransmissionType(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CVT = "cvt"
    DCT = "dct"
    SEMI_AUTO = "semi_automatic"


class DriveType(str, enum.Enum):
    FWD = "fwd"
    RWD = "rwd"
    AWD = "awd"
    FOUR_WD = "4wd"


class BodyType(str, enum.Enum):
    SEDAN = "sedan"
    HATCHBACK = "hatchback"
    SUV = "suv"
    CROSSOVER = "crossover"
    COUPE = "coupe"
    CONVERTIBLE = "convertible"
    WAGON = "wagon"
    VAN = "van"
    PICKUP = "pickup"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"
    OTHER = "other"


class VehicleCondition(str, enum.Enum):
    NEW = "new"
    USED = "used"
    CERTIFIED = "certified"
    DAMAGED = "damaged"
    SALVAGE = "salvage"


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class NegotiationStatus(str, enum.Enum):
    OPEN = "open"
    COUNTERED = "countered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class VehicleBrand:
    brand_id: str = field(default_factory=_id)
    name: str = ""
    country: str = ""
    logo_url: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "brand_id": self.brand_id,
            "name": self.name,
            "country": self.country,
            "logo_url": self.logo_url,
            "created_at": self.created_at,
        }


@dataclass
class VehicleModel:
    model_id: str = field(default_factory=_id)
    brand_id: str = ""
    name: str = ""
    category: CatalogCategory = CatalogCategory.CARS
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "brand_id": self.brand_id,
            "name": self.name,
            "category": self.category.value,
            "created_at": self.created_at,
        }


@dataclass
class Generation:
    generation_id: str = field(default_factory=_id)
    model_id: str = ""
    name: str = ""
    year_from: int = 0
    year_to: int = 0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "model_id": self.model_id,
            "name": self.name,
            "year_from": self.year_from,
            "year_to": self.year_to,
            "created_at": self.created_at,
        }


@dataclass
class Engine:
    engine_id: str = field(default_factory=_id)
    name: str = ""
    displacement_cc: int = 0
    power_hp: float = 0.0
    fuel_type: FuelType = FuelType.PETROL
    cylinders: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "name": self.name,
            "displacement_cc": self.displacement_cc,
            "power_hp": self.power_hp,
            "fuel_type": self.fuel_type.value,
            "cylinders": self.cylinders,
        }


@dataclass
class Transmission:
    transmission_id: str = field(default_factory=_id)
    name: str = ""
    transmission_type: TransmissionType = TransmissionType.AUTOMATIC
    gears: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "transmission_id": self.transmission_id,
            "name": self.name,
            "transmission_type": self.transmission_type.value,
            "gears": self.gears,
        }


@dataclass
class Configuration:
    configuration_id: str = field(default_factory=_id)
    generation_id: str = ""
    name: str = ""
    engine: Engine | None = None
    transmission: Transmission | None = None
    drive_type: DriveType = DriveType.FWD
    body_type: BodyType = BodyType.SEDAN
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration_id": self.configuration_id,
            "generation_id": self.generation_id,
            "name": self.name,
            "engine": self.engine.to_dict() if self.engine else None,
            "transmission": self.transmission.to_dict() if self.transmission else None,
            "drive_type": self.drive_type.value,
            "body_type": self.body_type.value,
            "created_at": self.created_at,
        }


@dataclass
class VIN:
    vin: str = ""
    valid: bool = False
    wmi: str = ""
    vds: str = ""
    vis: str = ""
    year: int | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vin": self.vin,
            "valid": self.valid,
            "wmi": self.wmi,
            "vds": self.vds,
            "vis": self.vis,
            "year": self.year,
            "detail": self.detail,
        }


@dataclass
class InspectionReport:
    report_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    inspector: str = ""
    score: float = 0.0
    condition: VehicleCondition = VehicleCondition.USED
    findings: list[str] = field(default_factory=list)
    passed: bool = True
    report_url: str = ""
    inspected_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "vehicle_id": self.vehicle_id,
            "inspector": self.inspector,
            "score": self.score,
            "condition": self.condition.value,
            "findings": list(self.findings),
            "passed": self.passed,
            "report_url": self.report_url,
            "inspected_at": self.inspected_at,
        }


@dataclass
class PriceHistory:
    entry_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    price: float = 0.0
    currency: str = "USD"
    reason: str = ""
    recorded_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "vehicle_id": self.vehicle_id,
            "price": self.price,
            "currency": self.currency,
            "reason": self.reason,
            "recorded_at": self.recorded_at,
        }


@dataclass
class Favorite:
    favorite_id: str = field(default_factory=_id)
    buyer_id: str = ""
    vehicle_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "favorite_id": self.favorite_id,
            "buyer_id": self.buyer_id,
            "vehicle_id": self.vehicle_id,
            "created_at": self.created_at,
        }


@dataclass
class Garage:
    garage_id: str = field(default_factory=_id)
    buyer_id: str = ""
    name: str = "My Garage"
    vehicle_ids: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "garage_id": self.garage_id,
            "buyer_id": self.buyer_id,
            "name": self.name,
            "vehicle_ids": list(self.vehicle_ids),
            "created_at": self.created_at,
        }


@dataclass
class Buyer:
    buyer_id: str = field(default_factory=_id)
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    region: str = ""
    preferences: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "buyer_id": self.buyer_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "region": self.region,
            "preferences": dict(self.preferences),
            "created_at": self.created_at,
        }


@dataclass
class BuyerRequest:
    request_id: str = field(default_factory=_id)
    buyer_id: str = ""
    vehicle_id: str = ""
    message: str = ""
    status: str = "open"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "buyer_id": self.buyer_id,
            "vehicle_id": self.vehicle_id,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class Appointment:
    appointment_id: str = field(default_factory=_id)
    buyer_id: str = ""
    dealer_id: str = ""
    vehicle_id: str = ""
    scheduled_at: float = 0.0
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "appointment_id": self.appointment_id,
            "buyer_id": self.buyer_id,
            "dealer_id": self.dealer_id,
            "vehicle_id": self.vehicle_id,
            "scheduled_at": self.scheduled_at,
            "status": self.status.value,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class Negotiation:
    negotiation_id: str = field(default_factory=_id)
    buyer_id: str = ""
    dealer_id: str = ""
    vehicle_id: str = ""
    offer_price: float = 0.0
    counter_price: float | None = None
    currency: str = "USD"
    status: NegotiationStatus = NegotiationStatus.OPEN
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "negotiation_id": self.negotiation_id,
            "buyer_id": self.buyer_id,
            "dealer_id": self.dealer_id,
            "vehicle_id": self.vehicle_id,
            "offer_price": self.offer_price,
            "counter_price": self.counter_price,
            "currency": self.currency,
            "status": self.status.value,
            "history": list(self.history),
            "created_at": self.created_at,
        }
