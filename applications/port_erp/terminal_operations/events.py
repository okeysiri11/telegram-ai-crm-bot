# Sprint 9.3 — Terminal operations events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class TruckArrivedEvent(BaseEvent):
    visit_id: str = ""
    gate_id: str = ""
    plate_number: str = ""
    terminal_id: str = ""


@dataclass(kw_only=True)
class TruckDepartedEvent(BaseEvent):
    visit_id: str = ""
    gate_id: str = ""
    plate_number: str = ""
    terminal_id: str = ""


@dataclass(kw_only=True)
class ContainerStoredEvent(BaseEvent):
    container_id: str = ""
    slot_id: str = ""
    block_id: str = ""
    terminal_id: str = ""


@dataclass(kw_only=True)
class ContainerMovedEvent(BaseEvent):
    container_id: str = ""
    from_slot_id: str = ""
    to_slot_id: str = ""
    terminal_id: str = ""


@dataclass(kw_only=True)
class CraneAssignedEvent(BaseEvent):
    assignment_id: str = ""
    crane_id: str = ""
    vessel_id: str = ""
    berth_id: str = ""


@dataclass(kw_only=True)
class CraneFinishedEvent(BaseEvent):
    assignment_id: str = ""
    crane_id: str = ""
    vessel_id: str = ""


@dataclass(kw_only=True)
class WarehouseUpdatedEvent(BaseEvent):
    warehouse_id: str = ""
    operation: str = ""
    reference: str = ""


@dataclass(kw_only=True)
class GateApprovedEvent(BaseEvent):
    visit_id: str = ""
    gate_id: str = ""
    plate_number: str = ""


@dataclass(kw_only=True)
class GateRejectedEvent(BaseEvent):
    visit_id: str = ""
    gate_id: str = ""
    plate_number: str = ""
    reason: str = ""
