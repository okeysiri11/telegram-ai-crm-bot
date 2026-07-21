# Sprint 9.2 — Tracking domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from applications.port_erp.shared.models import GeofenceType, TrackAssetType


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


@dataclass
class Position:
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_m: float = 0.0
    speed_knots: float = 0.0
    heading_deg: float = 0.0
    recorded_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_m": self.altitude_m,
            "speed_knots": self.speed_knots,
            "heading_deg": self.heading_deg,
            "recorded_at": self.recorded_at,
        }


@dataclass
class LivePosition:
    position_id: str = field(default_factory=_id)
    asset_type: TrackAssetType = TrackAssetType.VESSEL
    asset_id: str = ""
    position: Position = field(default_factory=Position)
    destination: str = ""
    last_checkpoint: str = ""
    eta: float = 0.0
    etd: float = 0.0
    source: str = "ais"
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "position_id": self.position_id,
            "asset_type": self.asset_type.value,
            "asset_id": self.asset_id,
            "position": self.position.to_dict(),
            "destination": self.destination,
            "last_checkpoint": self.last_checkpoint,
            "eta": self.eta,
            "etd": self.etd,
            "source": self.source,
            "metadata": dict(self.metadata),
            "updated_at": self.updated_at,
        }


@dataclass
class RoutePoint:
    latitude: float = 0.0
    longitude: float = 0.0
    recorded_at: float = field(default_factory=_ts)
    speed_knots: float = 0.0
    checkpoint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "recorded_at": self.recorded_at,
            "speed_knots": self.speed_knots,
            "checkpoint": self.checkpoint,
        }


@dataclass
class RouteHistory:
    route_id: str = field(default_factory=_id)
    asset_type: TrackAssetType = TrackAssetType.VESSEL
    asset_id: str = ""
    points: list[RoutePoint] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "asset_type": self.asset_type.value,
            "asset_id": self.asset_id,
            "points": [p.to_dict() for p in self.points],
            "created_at": self.created_at,
        }


@dataclass
class Geofence:
    geofence_id: str = field(default_factory=_id)
    name: str = ""
    fence_type: GeofenceType = GeofenceType.PORT
    related_id: str = ""
    center_lat: float = 0.0
    center_lon: float = 0.0
    radius_m: float = 500.0
    is_active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "geofence_id": self.geofence_id,
            "name": self.name,
            "fence_type": self.fence_type.value,
            "related_id": self.related_id,
            "center_lat": self.center_lat,
            "center_lon": self.center_lon,
            "radius_m": self.radius_m,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class TimelineEvent:
    event_id: str = field(default_factory=_id)
    asset_type: str = ""
    asset_id: str = ""
    event_type: str = ""
    title: str = ""
    detail: str = ""
    location: str = ""
    occurred_at: float = field(default_factory=_ts)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "asset_type": self.asset_type,
            "asset_id": self.asset_id,
            "event_type": self.event_type,
            "title": self.title,
            "detail": self.detail,
            "location": self.location,
            "occurred_at": self.occurred_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class ETAPrediction:
    prediction_id: str = field(default_factory=_id)
    asset_type: str = ""
    asset_id: str = ""
    eta: float = 0.0
    etd: float = 0.0
    confidence: float = 0.0
    delay_minutes: float = 0.0
    destination: str = ""
    method: str = "haversine_speed"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "asset_type": self.asset_type,
            "asset_id": self.asset_id,
            "eta": self.eta,
            "etd": self.etd,
            "confidence": self.confidence,
            "delay_minutes": self.delay_minutes,
            "destination": self.destination,
            "method": self.method,
            "created_at": self.created_at,
        }


@dataclass
class TruckTrack:
    truck_id: str = field(default_factory=_id)
    plate_number: str = ""
    carrier_id: str = ""
    container_id: str = ""
    status: str = "en_route"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "truck_id": self.truck_id,
            "plate_number": self.plate_number,
            "carrier_id": self.carrier_id,
            "container_id": self.container_id,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class ContainerLifecycleRecord:
    record_id: str = field(default_factory=_id)
    container_id: str = ""
    from_status: str = ""
    to_status: str = ""
    location: str = ""
    notes: str = ""
    occurred_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "container_id": self.container_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "location": self.location,
            "notes": self.notes,
            "occurred_at": self.occurred_at,
        }
