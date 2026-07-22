"""Smart transportation, logistics, AI mobility, smart city, dashboards, knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

DASHBOARD_TYPES = ["mobility", "transportation", "ev", "logistics", "smart_city", "sustainability"]
REGISTRY_TYPES = ["mobility", "transportation", "ev", "infrastructure", "logistics"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SmartTransportation:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def traffic_flow(self, *, corridor: str, vehicles_per_hour: int = 1200) -> dict[str, Any]:
        tid = _id("mp_flow")
        result = {
            "flow_id": tid,
            "corridor": corridor,
            "vehicles_per_hour": int(vehicles_per_hour),
            "level_of_service": "D" if vehicles_per_hour > 1800 else "C" if vehicles_per_hour > 1200 else "B",
            "at": _now(),
        }
        return self.store.mp_traffic_flow.save(tid, result)

    def congestion_prediction(self, *, region: str, horizon_min: int = 30) -> dict[str, Any]:
        pid = _id("mp_cong")
        result = {
            "prediction_id": pid,
            "region": region,
            "horizon_min": int(horizon_min),
            "congestion_probability": round(0.35 + (horizon_min % 40) / 100, 2),
            "at": _now(),
        }
        return self.store.mp_congestion.save(pid, result)

    def road_condition(self, *, road_id: str, condition: str = "good") -> dict[str, Any]:
        rid = _id("mp_road")
        result = {"condition_id": rid, "road_id": road_id, "condition": condition, "at": _now()}
        return self.store.mp_road_conditions.save(rid, result)

    def parking_availability(self, *, zone: str, available: int, capacity: int) -> dict[str, Any]:
        pid = _id("mp_park")
        result = {
            "parking_id": pid,
            "zone": zone,
            "available": int(available),
            "capacity": int(capacity),
            "occupancy_pct": round(100 * (1 - available / max(1, capacity)), 1),
            "at": _now(),
        }
        return self.store.mp_parking.save(pid, result)

    def public_transport(self, *, line: str, mode: str = "metro", headway_min: int = 5) -> dict[str, Any]:
        tid = _id("mp_pt")
        result = {"pt_id": tid, "line": line, "mode": mode, "headway_min": int(headway_min), "at": _now()}
        return self.store.mp_public_transport.save(tid, result)

    def emergency_route(self, *, origin: str, destination: str) -> dict[str, Any]:
        eid = _id("mp_emr")
        result = {
            "emergency_route_id": eid,
            "origin": origin,
            "destination": destination,
            "priority": "critical",
            "eta_min": 9.0,
            "at": _now(),
        }
        return self.store.mp_emergency_routes.save(eid, result)

    def status(self) -> dict[str, Any]:
        return {
            "flows": self.store.mp_traffic_flow.count(),
            "parking": self.store.mp_parking.count(),
            "public_transport": self.store.mp_public_transport.count(),
        }


class LogisticsIntelligence:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create_shipment(self, *, cargo: str, origin: str, destination: str) -> dict[str, Any]:
        if not cargo:
            raise ValidationError("cargo required")
        sid = _id("mp_ship")
        shipment = {
            "shipment_id": sid,
            "cargo": cargo,
            "origin": origin,
            "destination": destination,
            "status": "created",
            "created_at": _now(),
        }
        return self.store.mp_shipments.save(sid, shipment)

    def optimize_delivery(self, *, shipment_id: str, stops: list[str] | None = None) -> dict[str, Any]:
        if self.store.mp_shipments.get(shipment_id) is None:
            raise ValidationError("shipment not found")
        oid = _id("mp_del")
        result = {
            "delivery_id": oid,
            "shipment_id": shipment_id,
            "stops": stops or [],
            "cost_index": round(10 + len(stops or []) * 2.5, 1),
            "eta_min": round(25 + len(stops or []) * 12, 1),
            "at": _now(),
        }
        return self.store.mp_deliveries.save(oid, result)

    def track_cargo(self, *, shipment_id: str, lat: float, lon: float) -> dict[str, Any]:
        if self.store.mp_shipments.get(shipment_id) is None:
            raise ValidationError("shipment not found")
        tid = _id("mp_track")
        point = {"track_id": tid, "shipment_id": shipment_id, "lat": float(lat), "lon": float(lon), "at": _now()}
        return self.store.mp_cargo_tracking.save(tid, point)

    def dispatch(self, *, vehicle_id: str, shipment_id: str) -> dict[str, Any]:
        did = _id("mp_disp")
        job = {
            "dispatch_id": did,
            "vehicle_id": vehicle_id,
            "shipment_id": shipment_id,
            "status": "dispatched",
            "at": _now(),
        }
        return self.store.mp_dispatch.save(did, job)

    def warehouse_link(self, *, warehouse: str, shipment_id: str) -> dict[str, Any]:
        wid = _id("mp_wh")
        link = {"link_id": wid, "warehouse": warehouse, "shipment_id": shipment_id, "at": _now()}
        return self.store.mp_warehouses.save(wid, link)

    def status(self) -> dict[str, Any]:
        return {
            "shipments": self.store.mp_shipments.count(),
            "deliveries": self.store.mp_deliveries.count(),
            "dispatch": self.store.mp_dispatch.count(),
        }


class AIMobility:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def demand_forecast(self, *, region: str, horizon_h: int = 24) -> dict[str, Any]:
        fid = _id("mp_dem")
        result = {
            "forecast_id": fid,
            "region": region,
            "horizon_h": int(horizon_h),
            "demand_index": round(0.5 + (horizon_h % 20) / 40, 2),
            "at": _now(),
        }
        return self.store.mp_demand.save(fid, result)

    def recommend(self, *, user: str, intent: str = "commute") -> dict[str, Any]:
        rid = _id("mp_rec")
        result = {
            "recommendation_id": rid,
            "user": user,
            "intent": intent,
            "modes": ["metro", "ev_share"] if intent == "commute" else ["ride_share", "parking"],
            "at": _now(),
        }
        return self.store.mp_recommendations.save(rid, result)

    def travel_time(self, *, origin: str, destination: str) -> dict[str, Any]:
        tid = _id("mp_tt")
        result = {
            "prediction_id": tid,
            "origin": origin,
            "destination": destination,
            "travel_time_min": round(18 + abs(hash(origin + destination) % 40), 1),
            "at": _now(),
        }
        return self.store.mp_travel_time.save(tid, result)

    def energy_optimize(self, *, ev_id: str, route_km: float) -> dict[str, Any]:
        eid = _id("mp_eopt")
        result = {
            "optimization_id": eid,
            "ev_id": ev_id,
            "route_km": float(route_km),
            "kwh_estimate": round(route_km * 0.18, 2),
            "eco_score": 0.82,
            "at": _now(),
        }
        return self.store.mp_energy_opt.save(eid, result)

    def carbon_footprint(self, *, trips: int = 1, mode: str = "ev") -> dict[str, Any]:
        factors = {"ev": 0.05, "drive": 0.21, "metro": 0.04, "ride_share": 0.12}
        cid = _id("mp_co2")
        result = {
            "footprint_id": cid,
            "trips": int(trips),
            "mode": mode,
            "kg_co2e": round(trips * factors.get(mode, 0.15) * 10, 2),
            "at": _now(),
        }
        return self.store.mp_carbon.save(cid, result)

    def status(self) -> dict[str, Any]:
        return {
            "forecasts": self.store.mp_demand.count(),
            "recommendations": self.store.mp_recommendations.count(),
            "carbon": self.store.mp_carbon.count(),
        }


class SmartCity:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def register_asset(self, *, kind: str, name: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        kinds = ["infrastructure", "parking", "traffic_control", "road_sensor", "weather", "emergency"]
        if kind not in kinds:
            raise ValidationError(f"kind must be one of {kinds}")
        aid = _id("mp_city")
        asset = {"asset_id": aid, "kind": kind, "name": name, "meta": meta or {}, "created_at": _now()}
        return self.store.mp_city_assets.save(aid, asset)

    def urban_dashboard(self, *, city: str) -> dict[str, Any]:
        did = _id("mp_urban")
        board = {
            "dashboard_id": did,
            "city": city,
            "assets": self.store.mp_city_assets.count(),
            "parking_zones": self.store.mp_parking.count(),
            "sensors": len([a for a in self.store.mp_city_assets.list_all() if a.get("kind") == "road_sensor"]),
            "at": _now(),
        }
        return self.store.mp_urban_dash.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"assets": self.store.mp_city_assets.count(), "urban_dashboards": self.store.mp_urban_dash.count()}


class MobilityDashboard:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "mobility") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics_map = {
            "mobility": {"hubs": self.store.mp_hubs.count(), "plans": self.store.mp_travel_plans.count()},
            "transportation": {"flows": self.store.mp_traffic_flow.count(), "parking": self.store.mp_parking.count()},
            "ev": {"evs": self.store.mp_evs.count(), "sessions": self.store.mp_charge_sessions.count()},
            "logistics": {"shipments": self.store.mp_shipments.count(), "dispatch": self.store.mp_dispatch.count()},
            "smart_city": {"assets": self.store.mp_city_assets.count()},
            "sustainability": {"carbon": self.store.mp_carbon.count(), "energy_opt": self.store.mp_energy_opt.count()},
        }
        did = _id("mp_dash")
        board = {
            "dashboard_id": did,
            "dashboard_type": dashboard_type,
            "metrics": metrics_map[dashboard_type],
            "generated_at": _now(),
        }
        return self.store.mp_dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.mp_dashboards.count(), "types": self.types}


class MobilityKnowledge:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("mp_kg")
        entry = {
            "registry_id": rid,
            "registry_type": registry_type,
            "key": key,
            "payload": payload or {},
            "at": _now(),
        }
        return self.store.mp_registries.save(rid, entry)

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.mp_registries.count(), "types": self.types}
