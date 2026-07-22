# Sprint 10.5 — service, parts, maintenance models.

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


class PartKind(str, enum.Enum):
    OEM = "oem"
    AFTERMARKET = "aftermarket"
    USED = "used"


class RepairOrderStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    INSPECTING = "inspecting"
    ESTIMATED = "estimated"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class AppointmentStatus(str, enum.Enum):
    BOOKED = "booked"
    RESCHEDULED = "rescheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WarrantyKind(str, enum.Enum):
    MANUFACTURER = "manufacturer"
    EXTENDED = "extended"


@dataclass
class ServiceCenter:
    center_id: str = field(default_factory=_id)
    name: str = ""
    branch_code: str = ""
    address: str = ""
    timezone: str = "UTC"
    schedule: dict[str, str] = field(default_factory=lambda: {"mon-fri": "08:00-18:00", "sat": "09:00-14:00"})
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "center_id": self.center_id,
            "name": self.name,
            "branch_code": self.branch_code,
            "address": self.address,
            "timezone": self.timezone,
            "schedule": dict(self.schedule),
            "created_at": self.created_at,
        }


@dataclass
class Mechanic:
    mechanic_id: str = field(default_factory=_id)
    center_id: str = ""
    name: str = ""
    specialties: list[str] = field(default_factory=list)
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "mechanic_id": self.mechanic_id,
            "center_id": self.center_id,
            "name": self.name,
            "specialties": list(self.specialties),
            "active": self.active,
        }


@dataclass
class ServiceAdvisor:
    advisor_id: str = field(default_factory=_id)
    center_id: str = ""
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"advisor_id": self.advisor_id, "center_id": self.center_id, "name": self.name}


@dataclass
class RepairBay:
    bay_id: str = field(default_factory=_id)
    center_id: str = ""
    label: str = ""
    occupied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "bay_id": self.bay_id,
            "center_id": self.center_id,
            "label": self.label,
            "occupied": self.occupied,
        }


@dataclass
class RepairOrder:
    order_id: str = field(default_factory=_id)
    center_id: str = ""
    vehicle_id: str = ""
    vin: str = ""
    customer_id: str = ""
    advisor_id: str = ""
    mechanic_id: str = ""
    bay_id: str = ""
    status: RepairOrderStatus = RepairOrderStatus.ACCEPTED
    checklist: list[dict[str, Any]] = field(default_factory=list)
    estimate_amount: float = 0.0
    approved: bool = False
    progress_notes: list[str] = field(default_factory=list)
    parts_used: list[dict[str, Any]] = field(default_factory=list)
    currency: str = "USD"
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "center_id": self.center_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "customer_id": self.customer_id,
            "advisor_id": self.advisor_id,
            "mechanic_id": self.mechanic_id,
            "bay_id": self.bay_id,
            "status": self.status.value,
            "checklist": list(self.checklist),
            "estimate_amount": self.estimate_amount,
            "approved": self.approved,
            "progress_notes": list(self.progress_notes),
            "parts_used": list(self.parts_used),
            "currency": self.currency,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class MaintenancePlan:
    plan_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    name: str = ""
    interval_km: int = 10000
    interval_days: int = 365
    fleet_id: str = ""
    tasks: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "vehicle_id": self.vehicle_id,
            "name": self.name,
            "interval_km": self.interval_km,
            "interval_days": self.interval_days,
            "fleet_id": self.fleet_id,
            "tasks": list(self.tasks),
            "created_at": self.created_at,
        }


@dataclass
class MaintenanceSchedule:
    schedule_id: str = field(default_factory=_id)
    plan_id: str = ""
    vehicle_id: str = ""
    due_mileage_km: int = 0
    due_at: float = 0.0
    status: str = "scheduled"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "plan_id": self.plan_id,
            "vehicle_id": self.vehicle_id,
            "due_mileage_km": self.due_mileage_km,
            "due_at": self.due_at,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class ServiceAppointment:
    appointment_id: str = field(default_factory=_id)
    center_id: str = ""
    vehicle_id: str = ""
    customer_id: str = ""
    mechanic_id: str = ""
    bay_id: str = ""
    starts_at: float = 0.0
    ends_at: float = 0.0
    status: AppointmentStatus = AppointmentStatus.BOOKED
    service_type: str = "maintenance"
    notifications: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "appointment_id": self.appointment_id,
            "center_id": self.center_id,
            "vehicle_id": self.vehicle_id,
            "customer_id": self.customer_id,
            "mechanic_id": self.mechanic_id,
            "bay_id": self.bay_id,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "status": self.status.value,
            "service_type": self.service_type,
            "notifications": list(self.notifications),
            "created_at": self.created_at,
        }


@dataclass
class Supplier:
    supplier_id: str = field(default_factory=_id)
    name: str = ""
    country: str = ""
    rating: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "country": self.country,
            "rating": self.rating,
        }


@dataclass
class Part:
    part_id: str = field(default_factory=_id)
    sku: str = ""
    name: str = ""
    kind: PartKind = PartKind.OEM
    supplier_id: str = ""
    price: float = 0.0
    currency: str = "USD"
    compatible_makes: list[str] = field(default_factory=list)
    compatible_vins: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "part_id": self.part_id,
            "sku": self.sku,
            "name": self.name,
            "kind": self.kind.value,
            "supplier_id": self.supplier_id,
            "price": self.price,
            "currency": self.currency,
            "compatible_makes": list(self.compatible_makes),
            "compatible_vins": list(self.compatible_vins),
            "created_at": self.created_at,
        }


@dataclass
class PartsWarehouse:
    warehouse_id: str = field(default_factory=_id)
    center_id: str = ""
    name: str = ""
    location: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "warehouse_id": self.warehouse_id,
            "center_id": self.center_id,
            "name": self.name,
            "location": self.location,
        }


@dataclass
class StockItem:
    stock_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    part_id: str = ""
    quantity: int = 0
    reserved: int = 0
    min_quantity: int = 5

    def to_dict(self) -> dict[str, Any]:
        return {
            "stock_id": self.stock_id,
            "warehouse_id": self.warehouse_id,
            "part_id": self.part_id,
            "quantity": self.quantity,
            "reserved": self.reserved,
            "min_quantity": self.min_quantity,
            "available": max(0, self.quantity - self.reserved),
            "low_stock": self.quantity - self.reserved <= self.min_quantity,
        }


@dataclass
class PurchaseOrder:
    po_id: str = field(default_factory=_id)
    supplier_id: str = ""
    warehouse_id: str = ""
    lines: list[dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "po_id": self.po_id,
            "supplier_id": self.supplier_id,
            "warehouse_id": self.warehouse_id,
            "lines": list(self.lines),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class WarrantyPolicy:
    warranty_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    vin: str = ""
    kind: WarrantyKind = WarrantyKind.MANUFACTURER
    provider: str = ""
    starts_at: float = field(default_factory=_ts)
    ends_at: float = 0.0
    mileage_limit_km: int = 100000
    active: bool = True
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "warranty_id": self.warranty_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "kind": self.kind.value,
            "provider": self.provider,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "mileage_limit_km": self.mileage_limit_km,
            "active": self.active,
            "history": list(self.history),
        }


@dataclass
class WarrantyClaim:
    claim_id: str = field(default_factory=_id)
    warranty_id: str = ""
    order_id: str = ""
    description: str = ""
    status: str = "open"
    amount: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "warranty_id": self.warranty_id,
            "order_id": self.order_id,
            "description": self.description,
            "status": self.status,
            "amount": self.amount,
            "created_at": self.created_at,
        }


@dataclass
class DiagnosticReport:
    report_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    vin: str = ""
    obd_codes: list[str] = field(default_factory=list)
    inspection_notes: list[str] = field(default_factory=list)
    photos: list[str] = field(default_factory=list)
    damage: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    ai_summary: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "obd_codes": list(self.obd_codes),
            "inspection_notes": list(self.inspection_notes),
            "photos": list(self.photos),
            "damage": list(self.damage),
            "recommendations": list(self.recommendations),
            "ai_summary": self.ai_summary,
            "created_at": self.created_at,
        }


@dataclass
class VehicleServiceRecord:
    record_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    vin: str = ""
    kind: str = "maintenance"  # maintenance, repair, parts, warranty, invoice
    title: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    order_id: str = ""
    mileage_km: int = 0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "kind": self.kind,
            "title": self.title,
            "details": dict(self.details),
            "order_id": self.order_id,
            "mileage_km": self.mileage_km,
            "created_at": self.created_at,
        }
