# Sprint 8.5 — Export and logistics events.

from __future__ import annotations

from dataclasses import dataclass, field

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class IntlShipmentCreatedEvent(BaseEvent):
    shipment_id: str = ""
    order_id: str = ""
    destination_country: str = ""
    incoterm: str = ""


# Requirement alias
ShipmentCreatedEvent = IntlShipmentCreatedEvent


@dataclass(kw_only=True)
class ShipmentLoadedEvent(BaseEvent):
    shipment_id: str = ""
    container_id: str = ""
    quantity_tons: float = 0.0


@dataclass(kw_only=True)
class ShipmentDispatchedEvent(BaseEvent):
    shipment_id: str = ""
    carrier_id: str = ""
    origin_port_id: str = ""


@dataclass(kw_only=True)
class PortArrivedEvent(BaseEvent):
    shipment_id: str = ""
    port_id: str = ""


@dataclass(kw_only=True)
class CustomsClearedEvent(BaseEvent):
    shipment_id: str = ""
    declaration_id: str = ""
    country: str = ""


@dataclass(kw_only=True)
class ExportCompletedEvent(BaseEvent):
    shipment_id: str = ""
    order_id: str = ""
    destination_country: str = ""


@dataclass(kw_only=True)
class DeliveryConfirmedEvent(BaseEvent):
    shipment_id: str = ""
    location: str = ""


@dataclass(kw_only=True)
class RiskDetectedEvent(BaseEvent):
    shipment_id: str = ""
    risk_score: float = 0.0
    reasons: list[str] = field(default_factory=list)
