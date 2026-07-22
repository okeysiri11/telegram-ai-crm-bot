"""Mobility hub — network, routes, planner, optimizer, traffic, regional manager."""

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


class MobilityHub:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create_hub(self, *, name: str, region: str = "", city: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("hub name required")
        hid = _id("mp_hub")
        hub = {"hub_id": hid, "name": name, "region": region, "city": city, "created_at": _now()}
        return self.store.mp_hubs.save(hid, hub)

    def add_network_node(self, *, hub_id: str, node_type: str, name: str, lat: float = 0.0, lon: float = 0.0) -> dict[str, Any]:
        if self.store.mp_hubs.get(hub_id) is None:
            raise NotFoundError("hub", hub_id)
        nid = _id("mp_node")
        node = {
            "node_id": nid,
            "hub_id": hub_id,
            "node_type": node_type,
            "name": name,
            "lat": float(lat),
            "lon": float(lon),
            "created_at": _now(),
        }
        return self.store.mp_network.save(nid, node)

    def route_intelligence(self, *, origin: str, destination: str, mode: str = "drive") -> dict[str, Any]:
        if not origin or not destination:
            raise ValidationError("origin and destination required")
        rid = _id("mp_route")
        distance = 12.0 + abs(hash(origin + destination) % 80)
        duration = round(distance * (1.4 if mode == "drive" else 2.2), 1)
        route = {
            "route_id": rid,
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "distance_km": distance,
            "duration_min": duration,
            "congestion_index": round(0.2 + (distance % 10) / 20, 2),
            "at": _now(),
        }
        return self.store.mp_routes.save(rid, route)

    def travel_plan(self, *, origin: str, destination: str, preferences: dict[str, Any] | None = None) -> dict[str, Any]:
        route = self.route_intelligence(origin=origin, destination=destination, mode=(preferences or {}).get("mode", "drive"))
        pid = _id("mp_plan")
        plan = {
            "plan_id": pid,
            "origin": origin,
            "destination": destination,
            "route_id": route["route_id"],
            "legs": [{"mode": route["mode"], "duration_min": route["duration_min"]}],
            "preferences": preferences or {},
            "at": _now(),
        }
        return self.store.mp_travel_plans.save(pid, plan)

    def optimize_trip(self, *, plan_id: str) -> dict[str, Any]:
        plan = self.store.mp_travel_plans.get(plan_id)
        if plan is None:
            raise NotFoundError("travel_plan", plan_id)
        oid = _id("mp_opt")
        result = {
            "optimization_id": oid,
            "plan_id": plan_id,
            "saved_min": 8.5,
            "saved_km": 3.2,
            "strategy": "avoid_congestion",
            "at": _now(),
        }
        return self.store.mp_trip_opts.save(oid, result)

    def traffic_snapshot(self, *, region: str, congestion: float = 0.4) -> dict[str, Any]:
        tid = _id("mp_traf")
        snap = {
            "traffic_id": tid,
            "region": region,
            "congestion": float(congestion),
            "status": "heavy" if congestion > 0.7 else "moderate" if congestion > 0.4 else "light",
            "at": _now(),
        }
        return self.store.mp_traffic.save(tid, snap)

    def register_region(self, *, name: str, manager: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("region name required")
        rid = _id("mp_reg")
        region = {"region_id": rid, "name": name, "manager": manager, "created_at": _now()}
        return self.store.mp_regions.save(rid, region)

    def status(self) -> dict[str, Any]:
        return {
            "hubs": self.store.mp_hubs.count(),
            "network_nodes": self.store.mp_network.count(),
            "routes": self.store.mp_routes.count(),
            "plans": self.store.mp_travel_plans.count(),
        }
