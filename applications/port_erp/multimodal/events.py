# Sprint 9.5 — Logistics events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class BookingCreatedEvent(BaseEvent):
    booking_id: str = ""
    mode: str = ""
    origin: str = ""
    destination: str = ""


@dataclass(kw_only=True)
class BookingConfirmedEvent(BaseEvent):
    booking_id: str = ""
    carrier_id: str = ""
    quoted_amount: float = 0.0


@dataclass(kw_only=True)
class CarrierAssignedEvent(BaseEvent):
    order_id: str = ""
    carrier_id: str = ""
    mode: str = ""


@dataclass(kw_only=True)
class TransportStartedEvent(BaseEvent):
    order_id: str = ""
    booking_id: str = ""
    mode: str = ""


@dataclass(kw_only=True)
class TransportDelayedEvent(BaseEvent):
    order_id: str = ""
    delay_minutes: float = 0.0
    reason: str = ""


@dataclass(kw_only=True)
class TransportCompletedEvent(BaseEvent):
    order_id: str = ""
    booking_id: str = ""


@dataclass(kw_only=True)
class RouteOptimizedEvent(BaseEvent):
    route_id: str = ""
    optimized_for: str = ""
    total_cost: float = 0.0
    total_duration_hours: float = 0.0


@dataclass(kw_only=True)
class ShipmentTransferredEvent(BaseEvent):
    order_id: str = ""
    from_mode: str = ""
    to_mode: str = ""
    hub_id: str = ""
