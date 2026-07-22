# Sprint 9.3 — Terminal / yard / warehouse / gate / equipment / planning models.

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


class EquipmentType(str, enum.Enum):
    STS = "sts_crane"
    RTG = "rtg"
    RMG = "rmg"
    REACH_STACKER = "reach_stacker"
    FORKLIFT = "forklift"
    TERMINAL_TRUCK = "terminal_truck"
    TRAILER = "trailer"


class EquipmentStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    WORKING = "working"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class YardSlotStatus(str, enum.Enum):
    EMPTY = "empty"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    BLOCKED = "blocked"


class WarehouseOperationType(str, enum.Enum):
    RECEIVING = "receiving"
    STORAGE = "storage"
    PICKING = "picking"
    PACKING = "packing"
    CROSS_DOCK = "cross_dock"
    CYCLE_COUNT = "cycle_count"


class GateVisitStatus(str, enum.Enum):
    QUEUED = "queued"
    CHECKED_IN = "checked_in"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHECKED_OUT = "checked_out"


class PlanType(str, enum.Enum):
    BERTH = "berth"
    CRANE = "crane"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    YARD = "yard"
    WAREHOUSE = "warehouse"


class DispatchStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class YardBlock:
    block_id: str = field(default_factory=_id)
    terminal_id: str = ""
    name: str = ""
    rows: int = 0
    slots_per_row: int = 0
    max_tiers: int = 5
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "terminal_id": self.terminal_id,
            "name": self.name,
            "rows": self.rows,
            "slots_per_row": self.slots_per_row,
            "max_tiers": self.max_tiers,
            "created_at": self.created_at,
        }


@dataclass
class YardSlot:
    slot_id: str = field(default_factory=_id)
    block_id: str = ""
    terminal_id: str = ""
    row: int = 0
    bay: int = 0
    tier: int = 1
    status: YardSlotStatus = YardSlotStatus.EMPTY
    container_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "block_id": self.block_id,
            "terminal_id": self.terminal_id,
            "row": self.row,
            "bay": self.bay,
            "tier": self.tier,
            "status": self.status.value,
            "container_id": self.container_id,
            "created_at": self.created_at,
        }


@dataclass
class YardRelocation:
    relocation_id: str = field(default_factory=_id)
    container_id: str = ""
    from_slot_id: str = ""
    to_slot_id: str = ""
    reason: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relocation_id": self.relocation_id,
            "container_id": self.container_id,
            "from_slot_id": self.from_slot_id,
            "to_slot_id": self.to_slot_id,
            "reason": self.reason,
            "created_at": self.created_at,
        }


@dataclass
class WarehouseZone:
    zone_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    name: str = ""
    zone_type: str = "storage"
    capacity_units: int = 0
    used_units: int = 0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "warehouse_id": self.warehouse_id,
            "name": self.name,
            "zone_type": self.zone_type,
            "capacity_units": self.capacity_units,
            "used_units": self.used_units,
            "created_at": self.created_at,
        }


@dataclass
class InventoryItem:
    item_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    zone_id: str = ""
    sku: str = ""
    description: str = ""
    quantity: float = 0.0
    unit: str = "unit"
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "warehouse_id": self.warehouse_id,
            "zone_id": self.zone_id,
            "sku": self.sku,
            "description": self.description,
            "quantity": self.quantity,
            "unit": self.unit,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class StockMovement:
    movement_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    item_id: str = ""
    movement_type: str = "in"
    quantity: float = 0.0
    from_zone_id: str = ""
    to_zone_id: str = ""
    reference: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "movement_id": self.movement_id,
            "warehouse_id": self.warehouse_id,
            "item_id": self.item_id,
            "movement_type": self.movement_type,
            "quantity": self.quantity,
            "from_zone_id": self.from_zone_id,
            "to_zone_id": self.to_zone_id,
            "reference": self.reference,
            "created_at": self.created_at,
        }


@dataclass
class WarehouseTask:
    task_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    operation: WarehouseOperationType = WarehouseOperationType.RECEIVING
    reference: str = ""
    status: str = "open"
    notes: str = ""
    created_at: float = field(default_factory=_ts)
    completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "warehouse_id": self.warehouse_id,
            "operation": self.operation.value,
            "reference": self.reference,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class CycleCount:
    count_id: str = field(default_factory=_id)
    warehouse_id: str = ""
    zone_id: str = ""
    expected_qty: float = 0.0
    counted_qty: float = 0.0
    variance: float = 0.0
    status: str = "open"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "count_id": self.count_id,
            "warehouse_id": self.warehouse_id,
            "zone_id": self.zone_id,
            "expected_qty": self.expected_qty,
            "counted_qty": self.counted_qty,
            "variance": self.variance,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class GateAppointment:
    appointment_id: str = field(default_factory=_id)
    gate_id: str = ""
    terminal_id: str = ""
    plate_number: str = ""
    driver_name: str = ""
    container_id: str = ""
    scheduled_at: float = 0.0
    status: str = "scheduled"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "appointment_id": self.appointment_id,
            "gate_id": self.gate_id,
            "terminal_id": self.terminal_id,
            "plate_number": self.plate_number,
            "driver_name": self.driver_name,
            "container_id": self.container_id,
            "scheduled_at": self.scheduled_at,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class GateVisit:
    visit_id: str = field(default_factory=_id)
    gate_id: str = ""
    terminal_id: str = ""
    plate_number: str = ""
    driver_name: str = ""
    driver_id: str = ""
    appointment_id: str = ""
    container_id: str = ""
    status: GateVisitStatus = GateVisitStatus.QUEUED
    ocr_plate: str = ""
    qr_code: str = ""
    access_granted: bool = False
    rejection_reason: str = ""
    queue_position: int = 0
    checked_in_at: float = 0.0
    checked_out_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "visit_id": self.visit_id,
            "gate_id": self.gate_id,
            "terminal_id": self.terminal_id,
            "plate_number": self.plate_number,
            "driver_name": self.driver_name,
            "driver_id": self.driver_id,
            "appointment_id": self.appointment_id,
            "container_id": self.container_id,
            "status": self.status.value,
            "ocr_plate": self.ocr_plate,
            "qr_code": self.qr_code,
            "access_granted": self.access_granted,
            "rejection_reason": self.rejection_reason,
            "queue_position": self.queue_position,
            "checked_in_at": self.checked_in_at,
            "checked_out_at": self.checked_out_at,
            "created_at": self.created_at,
        }


@dataclass
class Equipment:
    equipment_id: str = field(default_factory=_id)
    terminal_id: str = ""
    name: str = ""
    equipment_type: EquipmentType = EquipmentType.FORKLIFT
    status: EquipmentStatus = EquipmentStatus.AVAILABLE
    next_maintenance_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "equipment_id": self.equipment_id,
            "terminal_id": self.terminal_id,
            "name": self.name,
            "equipment_type": self.equipment_type.value,
            "status": self.status.value,
            "next_maintenance_at": self.next_maintenance_at,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class CraneAssignment:
    assignment_id: str = field(default_factory=_id)
    crane_id: str = ""
    vessel_id: str = ""
    berth_id: str = ""
    voyage_id: str = ""
    status: str = "assigned"
    started_at: float = 0.0
    finished_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "crane_id": self.crane_id,
            "vessel_id": self.vessel_id,
            "berth_id": self.berth_id,
            "voyage_id": self.voyage_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "created_at": self.created_at,
        }


@dataclass
class DispatchJob:
    job_id: str = field(default_factory=_id)
    terminal_id: str = ""
    job_type: str = "move"
    container_id: str = ""
    equipment_id: str = ""
    from_location: str = ""
    to_location: str = ""
    status: DispatchStatus = DispatchStatus.PENDING
    created_at: float = field(default_factory=_ts)
    completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "terminal_id": self.terminal_id,
            "job_type": self.job_type,
            "container_id": self.container_id,
            "equipment_id": self.equipment_id,
            "from_location": self.from_location,
            "to_location": self.to_location,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class TerminalPlan:
    plan_id: str = field(default_factory=_id)
    terminal_id: str = ""
    plan_type: PlanType = PlanType.YARD
    title: str = ""
    resources: list[str] = field(default_factory=list)
    start_at: float = 0.0
    end_at: float = 0.0
    status: str = "draft"
    notes: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "terminal_id": self.terminal_id,
            "plan_type": self.plan_type.value,
            "title": self.title,
            "resources": list(self.resources),
            "start_at": self.start_at,
            "end_at": self.end_at,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
        }
