# Sprint 10.6 — logistics, transport, customs, import/export models.

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


class TransportMode(str, enum.Enum):
    TRUCK = "truck"
    TOW = "tow"
    RAIL = "rail"
    SEA = "sea"
    AIR = "air"
    MULTI = "multi"


class ShipmentKind(str, enum.Enum):
    PICKUP = "pickup"
    DELIVERY = "delivery"
    DOOR_TO_DOOR = "door_to_door"
    TERMINAL = "terminal"
    DEALER_TRANSFER = "dealer_transfer"
    FLEET_TRANSFER = "fleet_transfer"


class ShipmentStatus(str, enum.Enum):
    DRAFT = "draft"
    BOOKED = "booked"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in_transit"
    AT_BORDER = "at_border"
    CUSTOMS = "customs"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class CarrierKind(str, enum.Enum):
    COMPANY = "company"
    PRIVATE = "private"
    TOW = "tow"
    RAIL = "rail"
    SEA = "sea"
    AIR = "air"


@dataclass
class Carrier:
    carrier_id: str = field(default_factory=_id)
    name: str = ""
    kind: CarrierKind = CarrierKind.COMPANY
    modes: list[str] = field(default_factory=lambda: ["truck"])
    rating: float = 0.0
    countries: list[str] = field(default_factory=list)
    active: bool = True
    drivers: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "carrier_id": self.carrier_id,
            "name": self.name,
            "kind": self.kind.value,
            "modes": list(self.modes),
            "rating": self.rating,
            "countries": list(self.countries),
            "active": self.active,
            "drivers": list(self.drivers),
            "created_at": self.created_at,
        }


@dataclass
class VehicleShipment:
    shipment_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    vin: str = ""
    kind: ShipmentKind = ShipmentKind.DOOR_TO_DOOR
    mode: TransportMode = TransportMode.TRUCK
    status: ShipmentStatus = ShipmentStatus.DRAFT
    carrier_id: str = ""
    driver_id: str = ""
    origin: str = ""
    destination: str = ""
    origin_country: str = ""
    destination_country: str = ""
    pickup_at: float = 0.0
    eta: float = 0.0
    cost: float = 0.0
    currency: str = "USD"
    stops: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    route_id: str = ""
    tracking_id: str = ""
    customs_id: str = ""
    document_ids: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shipment_id": self.shipment_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "kind": self.kind.value,
            "mode": self.mode.value,
            "status": self.status.value,
            "carrier_id": self.carrier_id,
            "driver_id": self.driver_id,
            "origin": self.origin,
            "destination": self.destination,
            "origin_country": self.origin_country,
            "destination_country": self.destination_country,
            "pickup_at": self.pickup_at,
            "eta": self.eta,
            "cost": self.cost,
            "currency": self.currency,
            "stops": list(self.stops),
            "timeline": list(self.timeline),
            "route_id": self.route_id,
            "tracking_id": self.tracking_id,
            "customs_id": self.customs_id,
            "document_ids": list(self.document_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class TrackingSession:
    tracking_id: str = field(default_factory=_id)
    shipment_id: str = ""
    lat: float = 0.0
    lon: float = 0.0
    status: str = "idle"
    eta: float = 0.0
    geofences: list[dict[str, Any]] = field(default_factory=list)
    route_history: list[dict[str, Any]] = field(default_factory=list)
    notifications: list[dict[str, Any]] = field(default_factory=list)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tracking_id": self.tracking_id,
            "shipment_id": self.shipment_id,
            "lat": self.lat,
            "lon": self.lon,
            "status": self.status,
            "eta": self.eta,
            "geofences": list(self.geofences),
            "route_history": list(self.route_history),
            "notifications": list(self.notifications),
            "updated_at": self.updated_at,
        }


@dataclass
class OptimizedRoute:
    route_id: str = field(default_factory=_id)
    shipment_id: str = ""
    stops: list[dict[str, Any]] = field(default_factory=list)
    distance_km: float = 0.0
    duration_hours: float = 0.0
    fuel_cost: float = 0.0
    total_cost: float = 0.0
    border_crossings: list[str] = field(default_factory=list)
    weather_factor: float = 1.0
    traffic_factor: float = 1.0
    ai_notes: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "shipment_id": self.shipment_id,
            "stops": list(self.stops),
            "distance_km": self.distance_km,
            "duration_hours": self.duration_hours,
            "fuel_cost": self.fuel_cost,
            "total_cost": self.total_cost,
            "border_crossings": list(self.border_crossings),
            "weather_factor": self.weather_factor,
            "traffic_factor": self.traffic_factor,
            "ai_notes": list(self.ai_notes),
            "created_at": self.created_at,
        }


@dataclass
class TradeShipment:
    trade_id: str = field(default_factory=_id)
    direction: str = "import"  # import | export
    vehicle_id: str = ""
    vin: str = ""
    origin_country: str = ""
    destination_country: str = ""
    shipment_id: str = ""
    duties: float = 0.0
    taxes: float = 0.0
    permissions: list[str] = field(default_factory=list)
    certificates: list[str] = field(default_factory=list)
    regulations: list[str] = field(default_factory=list)
    status: str = "draft"
    currency: str = "USD"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "direction": self.direction,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "origin_country": self.origin_country,
            "destination_country": self.destination_country,
            "shipment_id": self.shipment_id,
            "duties": self.duties,
            "taxes": self.taxes,
            "permissions": list(self.permissions),
            "certificates": list(self.certificates),
            "regulations": list(self.regulations),
            "status": self.status,
            "currency": self.currency,
            "created_at": self.created_at,
        }


@dataclass
class CustomsDeclaration:
    customs_id: str = field(default_factory=_id)
    shipment_id: str = ""
    vin: str = ""
    broker_id: str = ""
    broker_name: str = ""
    checkpoint: str = ""
    status: str = "draft"  # draft, submitted, clearing, cleared, held
    documents: list[str] = field(default_factory=list)
    vin_valid: bool = False
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "customs_id": self.customs_id,
            "shipment_id": self.shipment_id,
            "vin": self.vin,
            "broker_id": self.broker_id,
            "broker_name": self.broker_name,
            "checkpoint": self.checkpoint,
            "status": self.status,
            "documents": list(self.documents),
            "vin_valid": self.vin_valid,
            "history": list(self.history),
            "created_at": self.created_at,
        }


@dataclass
class LogisticsDocument:
    document_id: str = field(default_factory=_id)
    shipment_id: str = ""
    doc_type: str = "cmr"  # cmr, bol, export_declaration, import_declaration, invoice, insurance, delivery_receipt
    title: str = ""
    body: str = ""
    signed: bool = False
    signed_by: str = ""
    signed_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "shipment_id": self.shipment_id,
            "doc_type": self.doc_type,
            "title": self.title,
            "body": self.body,
            "signed": self.signed,
            "signed_by": self.signed_by,
            "signed_at": self.signed_at,
            "created_at": self.created_at,
        }


@dataclass
class FleetMovement:
    movement_id: str = field(default_factory=_id)
    kind: str = "dealer"  # dealer, auction, warehouse, port, rail
    vehicle_ids: list[str] = field(default_factory=list)
    from_location: str = ""
    to_location: str = ""
    carrier_id: str = ""
    truck_schedule: dict[str, Any] = field(default_factory=dict)
    status: str = "planned"
    shipment_ids: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "movement_id": self.movement_id,
            "kind": self.kind,
            "vehicle_ids": list(self.vehicle_ids),
            "from_location": self.from_location,
            "to_location": self.to_location,
            "carrier_id": self.carrier_id,
            "truck_schedule": dict(self.truck_schedule),
            "status": self.status,
            "shipment_ids": list(self.shipment_ids),
            "created_at": self.created_at,
        }
