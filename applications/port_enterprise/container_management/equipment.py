"""Port equipment, automation, and digital twin."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

EQUIPMENT_TYPES = ["sts", "rtg", "rmg", "reach_stacker", "straddle", "tractor", "forklift"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PortEquipment:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(EQUIPMENT_TYPES)

    def register(self, *, name: str, equipment_type: str, yard_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("equipment name required")
        if equipment_type not in EQUIPMENT_TYPES:
            raise ValidationError(f"equipment_type must be one of {EQUIPMENT_TYPES}")
        eid = _id("cm_eq")
        return self.store.cm_equipment.save(
            eid,
            {
                "equipment_id": eid,
                "name": name,
                "equipment_type": equipment_type,
                "yard_id": yard_id,
                "health_score": 95.0,
                "status": "available",
                "created_at": _now(),
            },
        )

    def health(self, equipment_id: str, *, health_score: float) -> dict[str, Any]:
        eq = self.store.cm_equipment.get(equipment_id)
        if eq is None:
            raise NotFoundError("equipment", equipment_id)
        eq["health_score"] = float(health_score)
        eq["status"] = "maintenance" if health_score < 60 else eq.get("status", "available")
        eq["updated_at"] = _now()
        return self.store.cm_equipment.save(equipment_id, eq)

    def schedule_maintenance(self, equipment_id: str, *, due_at: str, work: str = "service") -> dict[str, Any]:
        if self.store.cm_equipment.get(equipment_id) is None:
            raise NotFoundError("equipment", equipment_id)
        mid = _id("cm_eqm")
        return self.store.cm_eq_maint.save(
            mid,
            {
                "schedule_id": mid,
                "equipment_id": equipment_id,
                "due_at": due_at,
                "work": work,
                "status": "scheduled",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "equipment": self.store.cm_equipment.count(),
            "maintenance_schedules": self.store.cm_eq_maint.count(),
            "types": self.types,
        }


class TerminalAutomation:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def assign_task(self, *, equipment_id: str, container_id: str, task_type: str = "move") -> dict[str, Any]:
        if self.store.cm_equipment.get(equipment_id) is None:
            raise NotFoundError("equipment", equipment_id)
        if self.store.cm_containers.get(container_id) is None:
            raise NotFoundError("container", container_id)
        tid = _id("cm_task")
        return self.store.cm_tasks.save(
            tid,
            {
                "task_id": tid,
                "equipment_id": equipment_id,
                "container_id": container_id,
                "task_type": task_type,
                "status": "assigned",
                "automated": True,
                "at": _now(),
            },
        )

    def dispatch(self, equipment_id: str, *, destination: str) -> dict[str, Any]:
        eq = self.store.cm_equipment.get(equipment_id)
        if eq is None:
            raise NotFoundError("equipment", equipment_id)
        eq["status"] = "dispatched"
        self.store.cm_equipment.save(equipment_id, eq)
        did = _id("cm_disp")
        return self.store.cm_dispatch.save(
            did,
            {
                "dispatch_id": did,
                "equipment_id": equipment_id,
                "destination": destination,
                "at": _now(),
            },
        )

    def route_container(self, *, container_id: str, path: list[str] | None = None) -> dict[str, Any]:
        if self.store.cm_containers.get(container_id) is None:
            raise NotFoundError("container", container_id)
        rid = _id("cm_rt")
        return self.store.cm_routes.save(
            rid,
            {
                "route_id": rid,
                "container_id": container_id,
                "path": path or ["gate", "yard", "quay"],
                "optimized": True,
                "at": _now(),
            },
        )

    def optimize_yard_ai(self, yard_id: str) -> dict[str, Any]:
        if self.store.cm_yards.get(yard_id) is None:
            raise NotFoundError("yard", yard_id)
        oid = _id("cm_aiyo")
        return self.store.cm_ai_yard.save(
            oid,
            {
                "optimization_id": oid,
                "yard_id": yard_id,
                "reshuffle_reduction_pct": 18.0,
                "queue_wait_reduction_pct": 12.0,
                "energy_saving_pct": 9.0,
                "at": _now(),
            },
        )

    def optimize_queue(self, *, queue_name: str, depth: int) -> dict[str, Any]:
        qid = _id("cm_qopt")
        return self.store.cm_queue_opts.save(
            qid,
            {
                "optimization_id": qid,
                "queue_name": queue_name,
                "depth": int(depth),
                "strategy": "shortest_job_first",
                "at": _now(),
            },
        )

    def optimize_energy(self, *, equipment_id: str) -> dict[str, Any]:
        if self.store.cm_equipment.get(equipment_id) is None:
            raise NotFoundError("equipment", equipment_id)
        eid = _id("cm_eopt")
        return self.store.cm_energy_opts.save(
            eid,
            {
                "optimization_id": eid,
                "equipment_id": equipment_id,
                "idle_reduction_pct": 15.0,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "tasks": self.store.cm_tasks.count(),
            "dispatches": self.store.cm_dispatch.count(),
            "routes": self.store.cm_routes.count(),
            "ai_yard_opts": self.store.cm_ai_yard.count(),
        }


class DigitalTwin:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def create_twin(self, *, terminal_name: str, yard_id: str = "") -> dict[str, Any]:
        if not terminal_name:
            raise ValidationError("terminal_name required")
        tid = _id("cm_twin")
        return self.store.cm_twins.save(
            tid,
            {
                "twin_id": tid,
                "terminal_name": terminal_name,
                "yard_id": yard_id,
                "live": True,
                "created_at": _now(),
            },
        )

    def visualize_equipment(self, twin_id: str) -> dict[str, Any]:
        if self.store.cm_twins.get(twin_id) is None:
            raise NotFoundError("twin", twin_id)
        vid = _id("cm_veq")
        return self.store.cm_twin_views.save(
            vid,
            {
                "view_id": vid,
                "twin_id": twin_id,
                "view_type": "equipment",
                "count": self.store.cm_equipment.count(),
                "at": _now(),
            },
        )

    def visualize_containers(self, twin_id: str) -> dict[str, Any]:
        if self.store.cm_twins.get(twin_id) is None:
            raise NotFoundError("twin", twin_id)
        vid = _id("cm_vctr")
        return self.store.cm_twin_views.save(
            vid,
            {
                "view_id": vid,
                "twin_id": twin_id,
                "view_type": "containers",
                "count": self.store.cm_containers.count(),
                "at": _now(),
            },
        )

    def live_yard(self, twin_id: str) -> dict[str, Any]:
        twin = self.store.cm_twins.get(twin_id)
        if twin is None:
            raise NotFoundError("twin", twin_id)
        lid = _id("cm_live")
        return self.store.cm_twin_live.save(
            lid,
            {
                "snapshot_id": lid,
                "twin_id": twin_id,
                "slots": self.store.cm_slots.count(),
                "equipment_active": self.store.cm_dispatch.count(),
                "at": _now(),
            },
        )

    def simulate(self, twin_id: str, *, hours: int = 24) -> dict[str, Any]:
        if self.store.cm_twins.get(twin_id) is None:
            raise NotFoundError("twin", twin_id)
        sid = _id("cm_sim")
        return self.store.cm_twin_sims.save(
            sid,
            {
                "simulation_id": sid,
                "twin_id": twin_id,
                "hours": int(hours),
                "projected_moves": int(hours) * 42,
                "at": _now(),
            },
        )

    def forecast_capacity(self, twin_id: str, *, days: int = 7) -> dict[str, Any]:
        if self.store.cm_twins.get(twin_id) is None:
            raise NotFoundError("twin", twin_id)
        fid = _id("cm_fc")
        return self.store.cm_twin_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "twin_id": twin_id,
                "days": int(days),
                "peak_utilization_pct": 82.5,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "twins": self.store.cm_twins.count(),
            "views": self.store.cm_twin_views.count(),
            "simulations": self.store.cm_twin_sims.count(),
        }
