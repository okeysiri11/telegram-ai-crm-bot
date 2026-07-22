# Sprint 9.5 — Shipping, forwarders, multimodal logistics models.

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
    SEA = "sea"
    ROAD = "road"
    RAIL = "rail"
    AIR = "air"
    MULTIMODAL = "multimodal"


class HubType(str, enum.Enum):
    ORIGIN = "origin"
    DESTINATION = "destination"
    TRANSIT_HUB = "transit_hub"
    PORT = "port"
    RAIL_TERMINAL = "rail_terminal"
    WAREHOUSE = "warehouse"
    CROSS_DOCK = "cross_dock"
    DISTRIBUTION_CENTER = "distribution_center"


class BookingStatus(str, enum.Enum):
    REQUEST = "request"
    QUOTE = "quote"
    RESERVATION = "reservation"
    CONFIRMATION = "confirmation"
    EXECUTION = "execution"
    COMPLETION = "completion"
    CANCELLATION = "cancellation"


class TransportOrderStatus(str, enum.Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    DISPATCHED = "dispatched"
    TRACKING = "tracking"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ScheduleStatus(str, enum.Enum):
    PLANNED = "planned"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


@dataclass
class ShippingSchedule:
    schedule_id: str = field(default_factory=_id)
    shipping_line_id: str = ""
    service_name: str = ""
    vessel_name: str = ""
    voyage_number: str = ""
    origin_port: str = ""
    destination_port: str = ""
    etd: float = 0.0
    eta: float = 0.0
    status: ScheduleStatus = ScheduleStatus.PLANNED
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "shipping_line_id": self.shipping_line_id,
            "service_name": self.service_name,
            "vessel_name": self.vessel_name,
            "voyage_number": self.voyage_number,
            "origin_port": self.origin_port,
            "destination_port": self.destination_port,
            "etd": self.etd,
            "eta": self.eta,
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class CarrierContract:
    contract_id: str = field(default_factory=_id)
    carrier_id: str = ""
    partner_id: str = ""
    mode: TransportMode = TransportMode.SEA
    rate_per_unit: float = 0.0
    currency: str = "USD"
    valid_from: float = 0.0
    valid_to: float = 0.0
    terms: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "carrier_id": self.carrier_id,
            "partner_id": self.partner_id,
            "mode": self.mode.value,
            "rate_per_unit": self.rate_per_unit,
            "currency": self.currency,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "terms": self.terms,
            "created_at": self.created_at,
        }


@dataclass
class RouteHub:
    hub_id: str = field(default_factory=_id)
    name: str = ""
    hub_type: HubType = HubType.PORT
    country: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hub_id": self.hub_id,
            "name": self.name,
            "hub_type": self.hub_type.value,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at,
        }


@dataclass
class RouteLeg:
    leg_id: str = field(default_factory=_id)
    from_hub_id: str = ""
    to_hub_id: str = ""
    mode: TransportMode = TransportMode.ROAD
    distance_km: float = 0.0
    duration_hours: float = 0.0
    cost: float = 0.0
    carrier_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "leg_id": self.leg_id,
            "from_hub_id": self.from_hub_id,
            "to_hub_id": self.to_hub_id,
            "mode": self.mode.value,
            "distance_km": self.distance_km,
            "duration_hours": self.duration_hours,
            "cost": self.cost,
            "carrier_id": self.carrier_id,
        }


@dataclass
class LogisticsRoute:
    route_id: str = field(default_factory=_id)
    name: str = ""
    origin_hub_id: str = ""
    destination_hub_id: str = ""
    legs: list[RouteLeg] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_duration_hours: float = 0.0
    total_cost: float = 0.0
    optimized_for: str = "eta"
    is_cross_border: bool = False
    door_to_door: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "name": self.name,
            "origin_hub_id": self.origin_hub_id,
            "destination_hub_id": self.destination_hub_id,
            "legs": [leg.to_dict() for leg in self.legs],
            "total_distance_km": self.total_distance_km,
            "total_duration_hours": self.total_duration_hours,
            "total_cost": self.total_cost,
            "optimized_for": self.optimized_for,
            "is_cross_border": self.is_cross_border,
            "door_to_door": self.door_to_door,
            "created_at": self.created_at,
        }


@dataclass
class TransportBooking:
    booking_id: str = field(default_factory=_id)
    forwarder_id: str = ""
    customer_id: str = ""
    shipping_line_id: str = ""
    carrier_id: str = ""
    route_id: str = ""
    container_id: str = ""
    mode: TransportMode = TransportMode.SEA
    status: BookingStatus = BookingStatus.REQUEST
    quoted_amount: float = 0.0
    currency: str = "USD"
    origin: str = ""
    destination: str = ""
    notes: str = ""
    created_at: float = field(default_factory=_ts)
    confirmed_at: float = 0.0
    completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "booking_id": self.booking_id,
            "forwarder_id": self.forwarder_id,
            "customer_id": self.customer_id,
            "shipping_line_id": self.shipping_line_id,
            "carrier_id": self.carrier_id,
            "route_id": self.route_id,
            "container_id": self.container_id,
            "mode": self.mode.value,
            "status": self.status.value,
            "quoted_amount": self.quoted_amount,
            "currency": self.currency,
            "origin": self.origin,
            "destination": self.destination,
            "notes": self.notes,
            "created_at": self.created_at,
            "confirmed_at": self.confirmed_at,
            "completed_at": self.completed_at,
        }


@dataclass
class TransportOrder:
    order_id: str = field(default_factory=_id)
    booking_id: str = ""
    carrier_id: str = ""
    route_id: str = ""
    container_id: str = ""
    mode: TransportMode = TransportMode.ROAD
    status: TransportOrderStatus = TransportOrderStatus.CREATED
    origin: str = ""
    destination: str = ""
    eta: float = 0.0
    delay_minutes: float = 0.0
    fleet_asset_id: str = ""
    created_at: float = field(default_factory=_ts)
    dispatched_at: float = 0.0
    completed_at: float = 0.0
    archived_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "booking_id": self.booking_id,
            "carrier_id": self.carrier_id,
            "route_id": self.route_id,
            "container_id": self.container_id,
            "mode": self.mode.value,
            "status": self.status.value,
            "origin": self.origin,
            "destination": self.destination,
            "eta": self.eta,
            "delay_minutes": self.delay_minutes,
            "fleet_asset_id": self.fleet_asset_id,
            "created_at": self.created_at,
            "dispatched_at": self.dispatched_at,
            "completed_at": self.completed_at,
            "archived_at": self.archived_at,
        }


@dataclass
class ConsolidationBatch:
    batch_id: str = field(default_factory=_id)
    forwarder_id: str = ""
    route_id: str = ""
    booking_ids: list[str] = field(default_factory=list)
    container_ids: list[str] = field(default_factory=list)
    status: str = "open"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "forwarder_id": self.forwarder_id,
            "route_id": self.route_id,
            "booking_ids": list(self.booking_ids),
            "container_ids": list(self.container_ids),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class FleetAssignment:
    assignment_id: str = field(default_factory=_id)
    order_id: str = ""
    asset_id: str = ""
    mode: TransportMode = TransportMode.ROAD
    status: str = "assigned"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "order_id": self.order_id,
            "asset_id": self.asset_id,
            "mode": self.mode.value,
            "status": self.status,
            "created_at": self.created_at,
        }
