# Sprint 9.1 — Port ERP foundation domain models.

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


class PortRole(str, enum.Enum):
    PORT_DIRECTOR = "port_director"
    TERMINAL_MANAGER = "terminal_manager"
    DISPATCHER = "dispatcher"
    WAREHOUSE_MANAGER = "warehouse_manager"
    CONTAINER_OPERATOR = "container_operator"
    CRANE_OPERATOR = "crane_operator"
    FORWARDER = "forwarder"
    SHIPPING_LINE = "shipping_line"
    BROKER = "broker"
    CUSTOMER = "customer"
    ADMINISTRATOR = "administrator"
    AI_EXECUTIVE = "ai_executive"


class VesselStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    APPROACHING = "approaching"
    ANCHORED = "anchored"
    DOCKED = "docked"
    LOADING = "loading"
    UNLOADING = "unloading"
    WAITING = "waiting"
    DEPARTED = "departed"
    COMPLETED = "completed"
    # Sprint 9.1 aliases retained for compatibility
    EXPECTED = "scheduled"
    ARRIVED = "docked"
    BERTHED = "docked"
    WORKING = "loading"


class ContainerStatus(str, enum.Enum):
    CREATED = "created"
    BOOKED = "booked"
    LOADED = "loaded"
    AT_PORT = "at_port"
    ON_VESSEL = "on_vessel"
    IN_TRANSIT = "in_transit"
    TRANSSHIPMENT = "transshipment"
    CUSTOMS = "customs"
    ARRIVED = "arrived"
    WAREHOUSE = "warehouse"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    # Sprint 9.1 aliases
    EXPECTED = "created"
    RECEIVED = "at_port"
    IN_YARD = "warehouse"
    RELEASED = "out_for_delivery"


class GateStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class GeofenceType(str, enum.Enum):
    PORT = "port"
    TERMINAL = "terminal"
    BERTH = "berth"
    WAREHOUSE = "warehouse"
    CONTAINER_YARD = "container_yard"
    GATE = "gate"
    RAIL_TERMINAL = "rail_terminal"


class TrackAssetType(str, enum.Enum):
    VESSEL = "vessel"
    CONTAINER = "container"
    TRUCK = "truck"
    RAIL = "rail"


@dataclass
class Port:
    port_id: str = field(default_factory=_id)
    name: str = ""
    code: str = ""
    country: str = ""
    city: str = ""
    timezone: str = "UTC"
    is_active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "port_id": self.port_id,
            "name": self.name,
            "code": self.code,
            "country": self.country,
            "city": self.city,
            "timezone": self.timezone,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class Terminal:
    terminal_id: str = field(default_factory=_id)
    port_id: str = ""
    name: str = ""
    terminal_type: str = "container"
    capacity_teu: int = 0
    is_active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "terminal_id": self.terminal_id,
            "port_id": self.port_id,
            "name": self.name,
            "terminal_type": self.terminal_type,
            "capacity_teu": self.capacity_teu,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class Berth:
    berth_id: str = field(default_factory=_id)
    terminal_id: str = ""
    port_id: str = ""
    name: str = ""
    length_m: float = 0.0
    max_draft_m: float = 0.0
    status: str = "available"
    assigned_vessel_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "berth_id": self.berth_id,
            "terminal_id": self.terminal_id,
            "port_id": self.port_id,
            "name": self.name,
            "length_m": self.length_m,
            "max_draft_m": self.max_draft_m,
            "status": self.status,
            "assigned_vessel_id": self.assigned_vessel_id,
            "created_at": self.created_at,
        }


@dataclass
class Vessel:
    vessel_id: str = field(default_factory=_id)
    name: str = ""
    imo: str = ""
    call_sign: str = ""
    flag: str = ""
    vessel_type: str = "container"
    loa_m: float = 0.0
    draft_m: float = 0.0
    shipping_line_id: str = ""
    status: VesselStatus = VesselStatus.SCHEDULED
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vessel_id": self.vessel_id,
            "name": self.name,
            "imo": self.imo,
            "call_sign": self.call_sign,
            "flag": self.flag,
            "vessel_type": self.vessel_type,
            "loa_m": self.loa_m,
            "draft_m": self.draft_m,
            "shipping_line_id": self.shipping_line_id,
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class Voyage:
    voyage_id: str = field(default_factory=_id)
    vessel_id: str = ""
    voyage_number: str = ""
    origin_port_id: str = ""
    destination_port_id: str = ""
    eta: float = 0.0
    etd: float = 0.0
    ata: float = 0.0
    atd: float = 0.0
    berth_id: str = ""
    status: str = "planned"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "voyage_id": self.voyage_id,
            "vessel_id": self.vessel_id,
            "voyage_number": self.voyage_number,
            "origin_port_id": self.origin_port_id,
            "destination_port_id": self.destination_port_id,
            "eta": self.eta,
            "etd": self.etd,
            "ata": self.ata,
            "atd": self.atd,
            "berth_id": self.berth_id,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class Container:
    container_id: str = field(default_factory=_id)
    container_number: str = ""
    container_type: str = "40HC"
    iso_code: str = "45G1"
    owner: str = ""
    voyage_id: str = ""
    vessel_id: str = ""
    terminal_id: str = ""
    status: ContainerStatus = ContainerStatus.CREATED
    weight_kg: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "container_id": self.container_id,
            "container_number": self.container_number,
            "container_type": self.container_type,
            "iso_code": self.iso_code,
            "owner": self.owner,
            "voyage_id": self.voyage_id,
            "vessel_id": self.vessel_id,
            "terminal_id": self.terminal_id,
            "status": self.status.value,
            "weight_kg": self.weight_kg,
            "created_at": self.created_at,
        }


@dataclass
class Cargo:
    cargo_id: str = field(default_factory=_id)
    description: str = ""
    hs_code: str = ""
    container_id: str = ""
    voyage_id: str = ""
    customer_id: str = ""
    weight_tons: float = 0.0
    volume_cbm: float = 0.0
    status: str = "declared"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cargo_id": self.cargo_id,
            "description": self.description,
            "hs_code": self.hs_code,
            "container_id": self.container_id,
            "voyage_id": self.voyage_id,
            "customer_id": self.customer_id,
            "weight_tons": self.weight_tons,
            "volume_cbm": self.volume_cbm,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class Warehouse:
    warehouse_id: str = field(default_factory=_id)
    port_id: str = ""
    terminal_id: str = ""
    name: str = ""
    capacity_tons: float = 0.0
    used_tons: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "warehouse_id": self.warehouse_id,
            "port_id": self.port_id,
            "terminal_id": self.terminal_id,
            "name": self.name,
            "capacity_tons": self.capacity_tons,
            "used_tons": self.used_tons,
            "created_at": self.created_at,
        }


@dataclass
class Gate:
    gate_id: str = field(default_factory=_id)
    port_id: str = ""
    terminal_id: str = ""
    name: str = ""
    gate_type: str = "in"
    status: GateStatus = GateStatus.CLOSED
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "port_id": self.port_id,
            "terminal_id": self.terminal_id,
            "name": self.name,
            "gate_type": self.gate_type,
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class Carrier:
    carrier_id: str = field(default_factory=_id)
    name: str = ""
    mode: str = "truck"
    contact_email: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "carrier_id": self.carrier_id,
            "name": self.name,
            "mode": self.mode,
            "contact_email": self.contact_email,
            "created_at": self.created_at,
        }


@dataclass
class ShippingLine:
    shipping_line_id: str = field(default_factory=_id)
    name: str = ""
    scac: str = ""
    country: str = ""
    contact_email: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shipping_line_id": self.shipping_line_id,
            "name": self.name,
            "scac": self.scac,
            "country": self.country,
            "contact_email": self.contact_email,
            "created_at": self.created_at,
        }


@dataclass
class Customer:
    customer_id: str = field(default_factory=_id)
    name: str = ""
    email: str = ""
    company: str = ""
    country: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "country": self.country,
            "created_at": self.created_at,
        }


@dataclass
class Forwarder:
    forwarder_id: str = field(default_factory=_id)
    name: str = ""
    license_number: str = ""
    email: str = ""
    country: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "forwarder_id": self.forwarder_id,
            "name": self.name,
            "license_number": self.license_number,
            "email": self.email,
            "country": self.country,
            "created_at": self.created_at,
        }


@dataclass
class CustomsBroker:
    broker_id: str = field(default_factory=_id)
    name: str = ""
    license_number: str = ""
    email: str = ""
    country: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "broker_id": self.broker_id,
            "name": self.name,
            "license_number": self.license_number,
            "email": self.email,
            "country": self.country,
            "created_at": self.created_at,
        }


@dataclass
class PortOperator:
    operator_id: str = field(default_factory=_id)
    name: str = ""
    port_id: str = ""
    email: str = ""
    role: str = "operator"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id": self.operator_id,
            "name": self.name,
            "port_id": self.port_id,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at,
        }


@dataclass
class PortDocument:
    document_id: str = field(default_factory=_id)
    title: str = ""
    document_type: str = "general"
    related_id: str = ""
    issuer: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "document_type": self.document_type,
            "related_id": self.related_id,
            "issuer": self.issuer,
            "created_at": self.created_at,
        }


@dataclass
class Invoice:
    invoice_id: str = field(default_factory=_id)
    customer_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: str = "draft"
    description: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at,
        }
