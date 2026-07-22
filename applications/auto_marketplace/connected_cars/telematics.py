"""Telematics — GPS, trips, behavior, fuel/battery, OBD, events."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Telematics:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def track_gps(self, *, connected_vehicle_id: str, lat: float, lon: float, speed_kmh: float = 0.0) -> dict[str, Any]:
        vehicle = self.store.cc_vehicles.get(connected_vehicle_id)
        if vehicle is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        pid = _id("cc_gps")
        point = {
            "point_id": pid,
            "connected_vehicle_id": connected_vehicle_id,
            "vin": vehicle["vin"],
            "lat": float(lat),
            "lon": float(lon),
            "speed_kmh": float(speed_kmh),
            "at": _now(),
        }
        return self.store.cc_gps_points.save(pid, point)

    def start_trip(self, *, connected_vehicle_id: str, origin: str = "") -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        tid = _id("cc_trip")
        trip = {
            "trip_id": tid,
            "connected_vehicle_id": connected_vehicle_id,
            "origin": origin,
            "destination": "",
            "distance_km": 0.0,
            "fuel_liters": 0.0,
            "status": "active",
            "started_at": _now(),
        }
        return self.store.cc_trips.save(tid, trip)

    def end_trip(
        self,
        trip_id: str,
        *,
        destination: str = "",
        distance_km: float = 0.0,
        fuel_liters: float = 0.0,
        harsh_events: int = 0,
    ) -> dict[str, Any]:
        trip = self.store.cc_trips.get(trip_id)
        if trip is None:
            raise NotFoundError("trip", trip_id)
        trip["destination"] = destination
        trip["distance_km"] = float(distance_km)
        trip["fuel_liters"] = float(fuel_liters)
        trip["harsh_events"] = int(harsh_events)
        trip["status"] = "completed"
        trip["ended_at"] = _now()
        score = max(0.0, 100.0 - harsh_events * 8 - (fuel_liters / max(1.0, distance_km)) * 20)
        trip["driving_behavior_score"] = round(score, 1)
        self.store.cc_trips.save(trip_id, trip)
        rid = _id("cc_route")
        analytics = {
            "route_id": rid,
            "trip_id": trip_id,
            "distance_km": trip["distance_km"],
            "efficiency": round(distance_km / max(0.1, fuel_liters), 2) if fuel_liters else 0.0,
            "behavior_score": trip["driving_behavior_score"],
            "at": _now(),
        }
        self.store.cc_route_analytics.save(rid, analytics)
        return trip

    def monitor_fuel(self, *, connected_vehicle_id: str, level_pct: float, liters: float = 0.0) -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        fid = _id("cc_fuel")
        reading = {
            "fuel_id": fid,
            "connected_vehicle_id": connected_vehicle_id,
            "level_pct": float(level_pct),
            "liters": float(liters),
            "at": _now(),
        }
        return self.store.cc_fuel.save(fid, reading)

    def monitor_battery(self, *, connected_vehicle_id: str, soc_pct: float, voltage: float = 12.4) -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        bid = _id("cc_batt")
        reading = {
            "battery_id": bid,
            "connected_vehicle_id": connected_vehicle_id,
            "soc_pct": float(soc_pct),
            "voltage": float(voltage),
            "at": _now(),
        }
        return self.store.cc_battery.save(bid, reading)

    def obd_snapshot(self, *, connected_vehicle_id: str, codes: list[str] | None = None, rpm: int = 0, coolant: float = 90.0) -> dict[str, Any]:
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        oid = _id("cc_obd")
        snap = {
            "obd_id": oid,
            "connected_vehicle_id": connected_vehicle_id,
            "dtc_codes": codes or [],
            "rpm": int(rpm),
            "coolant_c": float(coolant),
            "engine_ok": not bool(codes),
            "at": _now(),
        }
        return self.store.cc_obd.save(oid, snap)

    def record_event(self, *, connected_vehicle_id: str, event_type: str, severity: str = "info", details: dict[str, Any] | None = None) -> dict[str, Any]:
        if not event_type:
            raise ValidationError("event_type required")
        if self.store.cc_vehicles.get(connected_vehicle_id) is None:
            raise NotFoundError("connected_vehicle", connected_vehicle_id)
        eid = _id("cc_evt")
        event = {
            "event_id": eid,
            "connected_vehicle_id": connected_vehicle_id,
            "event_type": event_type,
            "severity": severity,
            "details": details or {},
            "at": _now(),
        }
        return self.store.cc_events.save(eid, event)

    def status(self) -> dict[str, Any]:
        return {
            "gps_points": self.store.cc_gps_points.count(),
            "trips": self.store.cc_trips.count(),
            "obd": self.store.cc_obd.count(),
            "events": self.store.cc_events.count(),
        }
