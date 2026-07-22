"""Fleet management — Sprint 13.6."""

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


class FleetManagement:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create_fleet(self, *, name: str, operator: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("fleet name required")
        fid = _id("erp_fleet")
        fleet = {"fleet_id": fid, "name": name, "operator": operator, "created_at": _now()}
        return self.store.erp_fleets.save(fid, fleet)

    def add_vehicle(self, *, fleet_id: str, vin: str, label: str = "") -> dict[str, Any]:
        if self.store.erp_fleets.get(fleet_id) is None:
            raise NotFoundError("fleet", fleet_id)
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required")
        vid = _id("erp_fveh")
        vehicle = {
            "fleet_vehicle_id": vid,
            "fleet_id": fleet_id,
            "vin": vin,
            "label": label or vin[-6:],
            "assigned_driver_id": "",
            "health_score": 90.0,
            "utilization": 0.0,
            "created_at": _now(),
        }
        return self.store.erp_fleet_vehicles.save(vid, vehicle)

    def register_driver(self, *, name: str, license_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("driver name required")
        did = _id("erp_drv")
        driver = {"driver_id": did, "name": name, "license_id": license_id, "status": "active", "created_at": _now()}
        return self.store.erp_drivers.save(did, driver)

    def assign_vehicle(self, *, fleet_vehicle_id: str, driver_id: str) -> dict[str, Any]:
        vehicle = self.store.erp_fleet_vehicles.get(fleet_vehicle_id)
        if vehicle is None:
            raise NotFoundError("fleet_vehicle", fleet_vehicle_id)
        if self.store.erp_drivers.get(driver_id) is None:
            raise NotFoundError("driver", driver_id)
        vehicle["assigned_driver_id"] = driver_id
        vehicle["updated_at"] = _now()
        return self.store.erp_fleet_vehicles.save(fleet_vehicle_id, vehicle)

    def log_trip(self, *, fleet_vehicle_id: str, distance_km: float, fuel_liters: float = 0.0) -> dict[str, Any]:
        vehicle = self.store.erp_fleet_vehicles.get(fleet_vehicle_id)
        if vehicle is None:
            raise NotFoundError("fleet_vehicle", fleet_vehicle_id)
        tid = _id("erp_trip")
        trip = {
            "trip_id": tid,
            "fleet_vehicle_id": fleet_vehicle_id,
            "vin": vehicle["vin"],
            "distance_km": float(distance_km),
            "fuel_liters": float(fuel_liters),
            "at": _now(),
        }
        self.store.erp_trips.save(tid, trip)
        util = min(100.0, float(vehicle.get("utilization") or 0) + float(distance_km) / 10.0)
        vehicle["utilization"] = round(util, 1)
        self.store.erp_fleet_vehicles.save(fleet_vehicle_id, vehicle)
        return trip

    def schedule_maintenance(self, *, fleet_vehicle_id: str, due_at: str, tasks: list[str] | None = None) -> dict[str, Any]:
        if self.store.erp_fleet_vehicles.get(fleet_vehicle_id) is None:
            raise NotFoundError("fleet_vehicle", fleet_vehicle_id)
        mid = _id("erp_fmaint")
        item = {
            "schedule_id": mid,
            "fleet_vehicle_id": fleet_vehicle_id,
            "due_at": due_at,
            "tasks": tasks or ["inspection"],
            "status": "scheduled",
            "created_at": _now(),
        }
        return self.store.erp_fleet_maintenance.save(mid, item)

    def dashboard(self, fleet_id: str) -> dict[str, Any]:
        vehicles = [v for v in self.store.erp_fleet_vehicles.list_all() if v.get("fleet_id") == fleet_id]
        trips = [t for t in self.store.erp_trips.list_all() if any(v["fleet_vehicle_id"] == t.get("fleet_vehicle_id") for v in vehicles)]
        avg_health = round(sum(float(v.get("health_score") or 0) for v in vehicles) / max(1, len(vehicles)), 1)
        return {
            "fleet_id": fleet_id,
            "vehicles": len(vehicles),
            "drivers": self.store.erp_drivers.count(),
            "trips": len(trips),
            "fuel_liters": round(sum(float(t.get("fuel_liters") or 0) for t in trips), 2),
            "avg_health": avg_health,
            "avg_utilization": round(sum(float(v.get("utilization") or 0) for v in vehicles) / max(1, len(vehicles)), 1),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "fleets": self.store.erp_fleets.count(),
            "vehicles": self.store.erp_fleet_vehicles.count(),
            "drivers": self.store.erp_drivers.count(),
            "trips": self.store.erp_trips.count(),
        }
