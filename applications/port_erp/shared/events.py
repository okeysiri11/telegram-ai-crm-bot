# Sprint 9.1 — Port ERP foundation events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class VesselArrivedEvent(BaseEvent):
    vessel_id: str = ""
    voyage_id: str = ""
    port_id: str = ""


@dataclass(kw_only=True)
class VesselDepartedEvent(BaseEvent):
    vessel_id: str = ""
    voyage_id: str = ""
    port_id: str = ""


@dataclass(kw_only=True)
class ContainerReceivedEvent(BaseEvent):
    container_id: str = ""
    terminal_id: str = ""
    container_number: str = ""


@dataclass(kw_only=True)
class ContainerReleasedEvent(BaseEvent):
    container_id: str = ""
    terminal_id: str = ""
    container_number: str = ""


@dataclass(kw_only=True)
class CargoLoadedEvent(BaseEvent):
    cargo_id: str = ""
    container_id: str = ""
    voyage_id: str = ""


@dataclass(kw_only=True)
class CargoUnloadedEvent(BaseEvent):
    cargo_id: str = ""
    container_id: str = ""
    voyage_id: str = ""


@dataclass(kw_only=True)
class BerthAssignedEvent(BaseEvent):
    berth_id: str = ""
    vessel_id: str = ""
    voyage_id: str = ""


@dataclass(kw_only=True)
class GateOpenedEvent(BaseEvent):
    gate_id: str = ""
    port_id: str = ""
    terminal_id: str = ""


@dataclass(kw_only=True)
class GateClosedEvent(BaseEvent):
    gate_id: str = ""
    port_id: str = ""
    terminal_id: str = ""
