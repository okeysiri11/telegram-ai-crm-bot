"""Fleet intelligence, smart services, dashboards, knowledge registries."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

DASHBOARD_TYPES = ["connected_fleet", "telematics", "predictive_maintenance", "vehicle_health"]
REGISTRY_TYPES = ["telemetry", "fleet", "iot", "diagnostics", "predictive"]
SERVICE_KINDS = ["insurance", "roadside", "charging", "fuel", "parking", "service_center"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FleetIntelligence:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def dashboard(self, *, fleet_id: str = "") -> dict[str, Any]:
        vehicles = self.store.cc_vehicles.list_all()
        if fleet_id:
            vehicles = [v for v in vehicles if v.get("fleet_id") == fleet_id]
        trips = self.store.cc_trips.list_all()
        fuel = self.store.cc_fuel.list_all()
        preds = self.store.cc_predictions.list_all()
        completed = [t for t in trips if t.get("status") == "completed"]
        avg_behavior = round(
            sum(float(t.get("driving_behavior_score") or 0) for t in completed) / max(1, len(completed)),
            1,
        )
        did = _id("cc_fi")
        board = {
            "dashboard_id": did,
            "fleet_id": fleet_id or "all",
            "vehicles": len(vehicles),
            "online": len([v for v in vehicles if v.get("connectivity") == "online"]),
            "trips": len(trips),
            "driver_performance": avg_behavior,
            "fuel_efficiency": round(
                sum(float(t.get("distance_km") or 0) for t in completed)
                / max(0.1, sum(float(t.get("fuel_liters") or 0) for t in completed)),
                2,
            )
            if completed
            else 0.0,
            "downtime_index": round(sum(float(p.get("failure_probability") or 0) for p in preds) / max(1, len(preds)), 3),
            "maintenance_kpis": {
                "alerts": self.store.cc_maintenance_alerts.count(),
                "predictions": len(preds),
            },
            "optimization_hint": "balance_utilization" if len(vehicles) > 2 else "expand_coverage",
            "at": _now(),
        }
        return self.store.cc_fleet_intel.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.cc_fleet_intel.count()}


class SmartServices:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.kinds = list(SERVICE_KINDS)

    def register(self, *, kind: str, name: str, lat: float = 0.0, lon: float = 0.0, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in self.kinds:
            raise ValidationError(f"kind must be one of {self.kinds}")
        if not name:
            raise ValidationError("name required")
        sid = _id("cc_svc")
        service = {
            "service_id": sid,
            "kind": kind,
            "name": name,
            "lat": float(lat),
            "lon": float(lon),
            "meta": meta or {},
            "created_at": _now(),
        }
        return self.store.cc_smart_services.save(sid, service)

    def locate(self, *, kind: str, near_lat: float = 0.0, near_lon: float = 0.0) -> list[dict[str, Any]]:
        items = [s for s in self.store.cc_smart_services.list_all() if s.get("kind") == kind]
        return sorted(
            items,
            key=lambda s: abs(float(s.get("lat") or 0) - near_lat) + abs(float(s.get("lon") or 0) - near_lon),
        )[:10]

    def status(self) -> dict[str, Any]:
        return {"services": self.store.cc_smart_services.count(), "kinds": self.kinds}


class ExecutiveDashboard:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "connected_fleet") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        if dashboard_type == "telematics":
            metrics: dict[str, Any] = {
                "gps_points": self.store.cc_gps_points.count(),
                "trips": self.store.cc_trips.count(),
                "events": self.store.cc_events.count(),
            }
        elif dashboard_type == "predictive_maintenance":
            metrics = {"predictions": self.store.cc_predictions.count(), "alerts": self.store.cc_maintenance_alerts.count()}
        elif dashboard_type == "vehicle_health":
            metrics = {"health_checks": self.store.cc_health.count(), "diagnostics": self.store.cc_diagnostics.count()}
        else:
            metrics = {
                "vehicles": self.store.cc_vehicles.count(),
                "iot_devices": self.store.cc_iot_devices.count(),
                "online": len([v for v in self.store.cc_vehicles.list_all() if v.get("connectivity") == "online"]),
            }
        did = _id("cc_dash")
        board = {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()}
        return self.store.cc_dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.cc_dashboards.count(), "types": self.types}


class KnowledgeRegistry:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("cc_reg")
        entry = {
            "registry_id": rid,
            "registry_type": registry_type,
            "key": key,
            "payload": payload or {},
            "at": _now(),
        }
        return self.store.cc_registries.save(rid, entry)

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.cc_registries.count(), "types": self.types}
