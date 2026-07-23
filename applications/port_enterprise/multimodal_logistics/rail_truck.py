"""Rail and truck logistics registries."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RailLogistics:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_network(self, *, name: str, region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("network name required")
        nid = _id("ml_net")
        return self.store.ml_rail_networks.save(
            nid, {"network_id": nid, "name": name, "region": region, "created_at": _now()}
        )

    def register_terminal(self, *, name: str, network_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("rail terminal name required")
        tid = _id("ml_rt")
        return self.store.ml_rail_terminals.save(
            tid, {"terminal_id": tid, "name": name, "network_id": network_id, "created_at": _now()}
        )

    def register_train(self, *, name: str, terminal_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("train name required")
        tid = _id("ml_trn")
        return self.store.ml_trains.save(
            tid, {"train_id": tid, "name": name, "terminal_id": terminal_id, "status": "ready", "created_at": _now()}
        )

    def register_wagon(self, *, code: str, train_id: str = "", capacity_teu: float = 2.0) -> dict[str, Any]:
        if not code:
            raise ValidationError("wagon code required")
        wid = _id("ml_wag")
        return self.store.ml_wagons.save(
            wid,
            {
                "wagon_id": wid,
                "code": code,
                "train_id": train_id,
                "capacity_teu": float(capacity_teu),
                "created_at": _now(),
            },
        )

    def register_locomotive(self, *, name: str, power_kw: float = 4000.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("locomotive name required")
        lid = _id("ml_loc")
        return self.store.ml_locomotives.save(
            lid, {"locomotive_id": lid, "name": name, "power_kw": float(power_kw), "created_at": _now()}
        )

    def schedule(self, *, train_id: str, origin: str, destination: str, departs_at: str) -> dict[str, Any]:
        if self.store.ml_trains.get(train_id) is None:
            raise NotFoundError("train", train_id)
        sid = _id("ml_rsch")
        return self.store.ml_rail_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "train_id": train_id,
                "origin": origin,
                "destination": destination,
                "departs_at": departs_at,
                "at": _now(),
            },
        )

    def track_cargo(self, *, train_id: str, cargo_ref: str, status: str = "in_transit") -> dict[str, Any]:
        if self.store.ml_trains.get(train_id) is None:
            raise NotFoundError("train", train_id)
        tid = _id("ml_rtrk")
        return self.store.ml_rail_tracking.save(
            tid,
            {
                "tracking_id": tid,
                "train_id": train_id,
                "cargo_ref": cargo_ref,
                "status": status,
                "at": _now(),
            },
        )

    def capacity_plan(self, *, network_id: str, teu: float, horizon_days: int = 30) -> dict[str, Any]:
        pid = _id("ml_rcap")
        return self.store.ml_rail_capacity.save(
            pid,
            {
                "plan_id": pid,
                "network_id": network_id,
                "teu": float(teu),
                "horizon_days": int(horizon_days),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "networks": self.store.ml_rail_networks.count(),
            "terminals": self.store.ml_rail_terminals.count(),
            "trains": self.store.ml_trains.count(),
            "wagons": self.store.ml_wagons.count(),
            "schedules": self.store.ml_rail_schedules.count(),
        }


class TruckLogistics:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_truck(self, *, plate: str, capacity_t: float = 20.0) -> dict[str, Any]:
        if not plate:
            raise ValidationError("plate required")
        tid = _id("ml_trk")
        return self.store.ml_trucks.save(
            tid,
            {
                "truck_id": tid,
                "plate": plate,
                "capacity_t": float(capacity_t),
                "fuel_l": 0.0,
                "status": "available",
                "created_at": _now(),
            },
        )

    def register_trailer(self, *, code: str, truck_id: str = "") -> dict[str, Any]:
        if not code:
            raise ValidationError("trailer code required")
        tid = _id("ml_trl")
        return self.store.ml_trailers.save(
            tid, {"trailer_id": tid, "code": code, "truck_id": truck_id, "created_at": _now()}
        )

    def register_driver(self, *, name: str, license_no: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("driver name required")
        did = _id("ml_drv")
        return self.store.ml_drivers.save(
            did, {"driver_id": did, "name": name, "license_no": license_no, "created_at": _now()}
        )

    def dispatch(self, *, truck_id: str, driver_id: str, destination: str) -> dict[str, Any]:
        if self.store.ml_trucks.get(truck_id) is None:
            raise NotFoundError("truck", truck_id)
        if self.store.ml_drivers.get(driver_id) is None:
            raise NotFoundError("driver", driver_id)
        did = _id("ml_tdsp")
        truck = self.store.ml_trucks.get(truck_id)
        truck["status"] = "dispatched"
        self.store.ml_trucks.save(truck_id, truck)
        return self.store.ml_truck_dispatch.save(
            did,
            {
                "dispatch_id": did,
                "truck_id": truck_id,
                "driver_id": driver_id,
                "destination": destination,
                "at": _now(),
            },
        )

    def plan_route(self, *, truck_id: str, origin: str, destination: str) -> dict[str, Any]:
        if self.store.ml_trucks.get(truck_id) is None:
            raise NotFoundError("truck", truck_id)
        rid = _id("ml_trte")
        return self.store.ml_truck_routes.save(
            rid,
            {
                "route_id": rid,
                "truck_id": truck_id,
                "origin": origin,
                "destination": destination,
                "planned": True,
                "at": _now(),
            },
        )

    def track(self, *, truck_id: str, lat: float, lon: float) -> dict[str, Any]:
        if self.store.ml_trucks.get(truck_id) is None:
            raise NotFoundError("truck", truck_id)
        tid = _id("ml_ttrk")
        return self.store.ml_truck_tracking.save(
            tid, {"tracking_id": tid, "truck_id": truck_id, "lat": float(lat), "lon": float(lon), "at": _now()}
        )

    def fuel(self, truck_id: str, *, liters: float) -> dict[str, Any]:
        truck = self.store.ml_trucks.get(truck_id)
        if truck is None:
            raise NotFoundError("truck", truck_id)
        truck["fuel_l"] = float(liters)
        return self.store.ml_trucks.save(truck_id, truck)

    def maintain(self, truck_id: str, *, work: str, due_at: str = "") -> dict[str, Any]:
        if self.store.ml_trucks.get(truck_id) is None:
            raise NotFoundError("truck", truck_id)
        mid = _id("ml_tmnt")
        return self.store.ml_truck_maint.save(
            mid,
            {
                "maintenance_id": mid,
                "truck_id": truck_id,
                "work": work,
                "due_at": due_at,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "trucks": self.store.ml_trucks.count(),
            "trailers": self.store.ml_trailers.count(),
            "drivers": self.store.ml_drivers.count(),
            "dispatches": self.store.ml_truck_dispatch.count(),
        }
