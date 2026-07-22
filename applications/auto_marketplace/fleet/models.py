# Sprint 10.7 — fleet, rental, corporate mobility, AI operations models.

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


class FleetVehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    RENTED = "rented"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class RentalKind(str, enum.Enum):
    SHORT = "short_term"
    LONG = "long_term"
    CORPORATE = "corporate"


class RentalStatus(str, enum.Enum):
    RESERVED = "reserved"
    ACTIVE = "active"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class FleetLeaseKind(str, enum.Enum):
    OPERATIONAL = "operational"
    FINANCIAL = "financial"


@dataclass
class FleetVehicle:
    fleet_vehicle_id: str = field(default_factory=_id)
    fleet_id: str = ""
    vehicle_id: str = ""
    vin: str = ""
    label: str = ""
    status: FleetVehicleStatus = FleetVehicleStatus.AVAILABLE
    assigned_driver_id: str = ""
    department: str = ""
    fuel_level_pct: float = 100.0
    mileage_km: int = 0
    tire_wear_pct: float = 0.0
    accidents: list[dict[str, Any]] = field(default_factory=list)
    costs: dict[str, float] = field(default_factory=lambda: {"fuel": 0.0, "maintenance": 0.0, "other": 0.0})
    revenue: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fleet_vehicle_id": self.fleet_vehicle_id,
            "fleet_id": self.fleet_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "label": self.label,
            "status": self.status.value,
            "assigned_driver_id": self.assigned_driver_id,
            "department": self.department,
            "fuel_level_pct": self.fuel_level_pct,
            "mileage_km": self.mileage_km,
            "tire_wear_pct": self.tire_wear_pct,
            "accidents": list(self.accidents),
            "costs": dict(self.costs),
            "revenue": self.revenue,
            "created_at": self.created_at,
        }


@dataclass
class FleetRegistry:
    fleet_id: str = field(default_factory=_id)
    name: str = ""
    owner_id: str = ""
    corporate: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fleet_id": self.fleet_id,
            "name": self.name,
            "owner_id": self.owner_id,
            "corporate": self.corporate,
            "created_at": self.created_at,
        }


@dataclass
class RentalContract:
    rental_id: str = field(default_factory=_id)
    fleet_vehicle_id: str = ""
    customer_id: str = ""
    kind: RentalKind = RentalKind.SHORT
    status: RentalStatus = RentalStatus.RESERVED
    starts_at: float = 0.0
    ends_at: float = 0.0
    daily_rate: float = 0.0
    total_price: float = 0.0
    currency: str = "USD"
    contract_text: str = ""
    damage_reports: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rental_id": self.rental_id,
            "fleet_vehicle_id": self.fleet_vehicle_id,
            "customer_id": self.customer_id,
            "kind": self.kind.value,
            "status": self.status.value,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "daily_rate": self.daily_rate,
            "total_price": self.total_price,
            "currency": self.currency,
            "contract_text": self.contract_text,
            "damage_reports": list(self.damage_reports),
            "created_at": self.created_at,
        }


@dataclass
class FleetLeaseContract:
    lease_id: str = field(default_factory=_id)
    fleet_vehicle_id: str = ""
    customer_id: str = ""
    kind: FleetLeaseKind = FleetLeaseKind.OPERATIONAL
    vehicle_price: float = 0.0
    residual_value: float = 0.0
    term_months: int = 36
    monthly_payment: float = 0.0
    schedule: list[dict[str, Any]] = field(default_factory=list)
    status: str = "quoted"
    insurance_policy: str = ""
    buyout_price: float = 0.0
    currency: str = "USD"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "fleet_vehicle_id": self.fleet_vehicle_id,
            "customer_id": self.customer_id,
            "kind": self.kind.value,
            "vehicle_price": self.vehicle_price,
            "residual_value": self.residual_value,
            "term_months": self.term_months,
            "monthly_payment": self.monthly_payment,
            "schedule": list(self.schedule),
            "status": self.status,
            "insurance_policy": self.insurance_policy,
            "buyout_price": self.buyout_price,
            "currency": self.currency,
            "created_at": self.created_at,
        }


@dataclass
class SubscriptionPlan:
    plan_id: str = field(default_factory=_id)
    name: str = ""
    monthly_fee: float = 0.0
    mileage_limit_km: int = 1500
    includes: list[str] = field(default_factory=list)
    currency: str = "USD"

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "monthly_fee": self.monthly_fee,
            "mileage_limit_km": self.mileage_limit_km,
            "includes": list(self.includes),
            "currency": self.currency,
        }


@dataclass
class MobilityBooking:
    booking_id: str = field(default_factory=_id)
    company_id: str = ""
    employee_id: str = ""
    fleet_vehicle_id: str = ""
    department: str = ""
    starts_at: float = 0.0
    ends_at: float = 0.0
    purpose: str = ""
    status: str = "booked"
    travel_request_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "booking_id": self.booking_id,
            "company_id": self.company_id,
            "employee_id": self.employee_id,
            "fleet_vehicle_id": self.fleet_vehicle_id,
            "department": self.department,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "purpose": self.purpose,
            "status": self.status,
            "travel_request_id": self.travel_request_id,
            "created_at": self.created_at,
        }


@dataclass
class TravelRequest:
    request_id: str = field(default_factory=_id)
    company_id: str = ""
    employee_id: str = ""
    department: str = ""
    destination: str = ""
    starts_at: float = 0.0
    ends_at: float = 0.0
    status: str = "pending"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "company_id": self.company_id,
            "employee_id": self.employee_id,
            "department": self.department,
            "destination": self.destination,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class FleetDriver:
    driver_id: str = field(default_factory=_id)
    name: str = ""
    license_id: str = ""
    license_expires_at: float = 0.0
    training: list[str] = field(default_factory=list)
    rating: float = 0.0
    violations: list[dict[str, Any]] = field(default_factory=list)
    hours_worked: float = 0.0
    performance_score: float = 0.0
    active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "driver_id": self.driver_id,
            "name": self.name,
            "license_id": self.license_id,
            "license_expires_at": self.license_expires_at,
            "training": list(self.training),
            "rating": self.rating,
            "violations": list(self.violations),
            "hours_worked": self.hours_worked,
            "performance_score": self.performance_score,
            "active": self.active,
            "created_at": self.created_at,
        }


@dataclass
class FleetDispatchJob:
    job_id: str = field(default_factory=_id)
    fleet_vehicle_id: str = ""
    driver_id: str = ""
    task: str = ""
    route: list[str] = field(default_factory=list)
    priority: int = 0
    emergency: bool = False
    status: str = "queued"
    scheduled_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "fleet_vehicle_id": self.fleet_vehicle_id,
            "driver_id": self.driver_id,
            "task": self.task,
            "route": list(self.route),
            "priority": self.priority,
            "emergency": self.emergency,
            "status": self.status,
            "scheduled_at": self.scheduled_at,
            "created_at": self.created_at,
        }


@dataclass
class TelematicsReading:
    reading_id: str = field(default_factory=_id)
    fleet_vehicle_id: str = ""
    lat: float = 0.0
    lon: float = 0.0
    speed_kmh: float = 0.0
    fuel_l_per_100km: float = 0.0
    mileage_km: int = 0
    battery_pct: float | None = None
    obd_codes: list[str] = field(default_factory=list)
    behavior_score: float = 80.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reading_id": self.reading_id,
            "fleet_vehicle_id": self.fleet_vehicle_id,
            "lat": self.lat,
            "lon": self.lon,
            "speed_kmh": self.speed_kmh,
            "fuel_l_per_100km": self.fuel_l_per_100km,
            "mileage_km": self.mileage_km,
            "battery_pct": self.battery_pct,
            "obd_codes": list(self.obd_codes),
            "behavior_score": self.behavior_score,
            "created_at": self.created_at,
        }
