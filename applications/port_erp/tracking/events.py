# Sprint 9.2 — Tracking events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class VesselPositionUpdatedEvent(BaseEvent):
    vessel_id: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    speed_knots: float = 0.0
    heading_deg: float = 0.0


@dataclass(kw_only=True)
class ContainerPositionUpdatedEvent(BaseEvent):
    container_id: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    status: str = ""


@dataclass(kw_only=True)
class TruckPositionUpdatedEvent(BaseEvent):
    truck_id: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    speed_knots: float = 0.0


@dataclass(kw_only=True)
class EnteredGeofenceEvent(BaseEvent):
    geofence_id: str = ""
    asset_type: str = ""
    asset_id: str = ""
    fence_type: str = ""


@dataclass(kw_only=True)
class ExitedGeofenceEvent(BaseEvent):
    geofence_id: str = ""
    asset_type: str = ""
    asset_id: str = ""
    fence_type: str = ""


@dataclass(kw_only=True)
class ETAChangedEvent(BaseEvent):
    asset_type: str = ""
    asset_id: str = ""
    eta: float = 0.0
    previous_eta: float = 0.0


@dataclass(kw_only=True)
class ETDChangedEvent(BaseEvent):
    asset_type: str = ""
    asset_id: str = ""
    etd: float = 0.0
    previous_etd: float = 0.0


@dataclass(kw_only=True)
class ArrivalPredictedEvent(BaseEvent):
    asset_type: str = ""
    asset_id: str = ""
    eta: float = 0.0
    confidence: float = 0.0
    destination: str = ""


@dataclass(kw_only=True)
class DelayDetectedEvent(BaseEvent):
    asset_type: str = ""
    asset_id: str = ""
    delay_minutes: float = 0.0
    reason: str = ""
