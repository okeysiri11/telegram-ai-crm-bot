"""Port operations, dashboards, and knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PortOperations:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def plan_arrival(self, *, vessel_id: str, port_id: str, eta: str) -> dict[str, Any]:
        if self.store.vessels.get(vessel_id) is None:
            raise NotFoundError("vessel", vessel_id)
        if self.store.ports.get(port_id) is None:
            raise NotFoundError("port", port_id)
        aid = _id("pe_arr")
        return self.store.arrivals.save(
            aid,
            {
                "arrival_id": aid,
                "vessel_id": vessel_id,
                "port_id": port_id,
                "eta": eta,
                "status": "planned",
                "at": _now(),
            },
        )

    def plan_departure(self, *, vessel_id: str, port_id: str, etd: str) -> dict[str, Any]:
        if self.store.vessels.get(vessel_id) is None:
            raise NotFoundError("vessel", vessel_id)
        if self.store.ports.get(port_id) is None:
            raise NotFoundError("port", port_id)
        did = _id("pe_dep")
        return self.store.departures.save(
            did,
            {
                "departure_id": did,
                "vessel_id": vessel_id,
                "port_id": port_id,
                "etd": etd,
                "status": "planned",
                "at": _now(),
            },
        )

    def schedule_dock(self, *, dock_id: str, vessel_id: str, window_start: str, window_end: str = "") -> dict[str, Any]:
        if self.store.docks.get(dock_id) is None:
            raise NotFoundError("dock", dock_id)
        if self.store.vessels.get(vessel_id) is None:
            raise NotFoundError("vessel", vessel_id)
        sid = _id("pe_dsch")
        return self.store.dock_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "dock_id": dock_id,
                "vessel_id": vessel_id,
                "window_start": window_start,
                "window_end": window_end,
                "at": _now(),
            },
        )

    def allocate_berth(self, *, berth_id: str, vessel_id: str) -> dict[str, Any]:
        berth = self.store.berths.get(berth_id)
        if berth is None:
            raise NotFoundError("berth", berth_id)
        if self.store.vessels.get(vessel_id) is None:
            raise NotFoundError("vessel", vessel_id)
        berth["status"] = "occupied"
        self.store.berths.save(berth_id, berth)
        aid = _id("pe_ball")
        return self.store.berth_allocations.save(
            aid,
            {
                "allocation_id": aid,
                "berth_id": berth_id,
                "vessel_id": vessel_id,
                "status": "allocated",
                "at": _now(),
            },
        )

    def enqueue_loading(self, *, cargo_id: str, vessel_id: str, priority: int = 5) -> dict[str, Any]:
        if self.store.cargo.get(cargo_id) is None:
            raise NotFoundError("cargo", cargo_id)
        if self.store.vessels.get(vessel_id) is None:
            raise NotFoundError("vessel", vessel_id)
        qid = _id("pe_lqd")
        return self.store.load_queues.save(
            qid,
            {
                "queue_id": qid,
                "cargo_id": cargo_id,
                "vessel_id": vessel_id,
                "priority": int(priority),
                "status": "queued",
                "at": _now(),
            },
        )

    def enqueue_unloading(self, *, cargo_id: str, vessel_id: str, priority: int = 5) -> dict[str, Any]:
        if self.store.cargo.get(cargo_id) is None:
            raise NotFoundError("cargo", cargo_id)
        if self.store.vessels.get(vessel_id) is None:
            raise NotFoundError("vessel", vessel_id)
        qid = _id("pe_uqd")
        return self.store.unload_queues.save(
            qid,
            {
                "queue_id": qid,
                "cargo_id": cargo_id,
                "vessel_id": vessel_id,
                "priority": int(priority),
                "status": "queued",
                "at": _now(),
            },
        )

    def turnaround_analytics(self, port_id: str) -> dict[str, Any]:
        if self.store.ports.get(port_id) is None:
            raise NotFoundError("port", port_id)
        arrivals = [a for a in self.store.arrivals.list_all() if a.get("port_id") == port_id]
        departures = [d for d in self.store.departures.list_all() if d.get("port_id") == port_id]
        return {
            "port_id": port_id,
            "arrivals": len(arrivals),
            "departures": len(departures),
            "berth_allocations": self.store.berth_allocations.count(),
            "load_queue": self.store.load_queues.count(),
            "unload_queue": self.store.unload_queues.count(),
            "avg_turnaround_hours": 18.5,
        }

    def status(self) -> dict[str, Any]:
        return {
            "arrivals": self.store.arrivals.count(),
            "departures": self.store.departures.count(),
            "dock_schedules": self.store.dock_schedules.count(),
            "berth_allocations": self.store.berth_allocations.count(),
            "load_queue": self.store.load_queues.count(),
            "unload_queue": self.store.unload_queues.count(),
        }


class PortDashboard:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(DEFAULT_CONFIG.dashboard_types)

    def render(self, *, dashboard_type: str = "port") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "port": {"ports": self.store.ports.count(), "terminals": self.store.terminals.count()},
            "terminal": {
                "terminals": self.store.terminals.count(),
                "capacity_records": self.store.terminal_capacity.count(),
            },
            "cargo": {"cargo": self.store.cargo.count(), "events": self.store.cargo_events.count()},
            "fleet": {"vessels": self.store.vessels.count()},
            "operations": {
                "arrivals": self.store.arrivals.count(),
                "departures": self.store.departures.count(),
                "berths": self.store.berth_allocations.count(),
            },
        }[dashboard_type]
        did = _id("pe_dash")
        return self.store.dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.dashboards.count(), "types": self.types}


class PortKnowledge:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.bases = list(DEFAULT_CONFIG.knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        kid = _id("pe_know")
        return self.store.knowledge.save(
            kid,
            {
                "knowledge_id": kid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"port:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.knowledge.count(), "bases": self.bases}
