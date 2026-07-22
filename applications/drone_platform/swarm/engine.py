"""Swarm intelligence — multi-UAV coordination (Sprint 11.7)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SwarmIntelligence:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_swarm_mission(
        self,
        *,
        name: str,
        fleet_ids: list[str],
        formation: str = "line",
        leader_id: str = "",
        tasks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if len(fleet_ids) < 2:
            raise ValidationError("Swarm mission requires at least 2 aircraft")
        sid = f"swm_{uuid.uuid4().hex[:12]}"
        leader = leader_id or fleet_ids[0]
        roles = [{"fleet_id": fid, "role": "leader" if fid == leader else "follower"} for fid in fleet_ids]
        item = {
            "swarm_id": sid,
            "name": name,
            "fleet_ids": list(fleet_ids),
            "formation": formation,
            "leader_id": leader,
            "roles": roles,
            "tasks": list(tasks or []),
            "status": "formed",
            "health": "ok",
            "created_at": _now(),
        }
        self.store.swarm_missions.save(sid, item)
        return item

    def get(self, swarm_id: str) -> dict[str, Any]:
        item = self.store.swarm_missions.get(swarm_id)
        if item is None:
            raise NotFoundError("swarm_mission", swarm_id)
        return item

    def formation_flight(self, swarm_id: str, *, formation: str) -> dict[str, Any]:
        swarm = self.get(swarm_id)
        swarm["formation"] = formation
        swarm["status"] = "formation_flight"
        self.store.swarm_missions.save(swarm_id, swarm)
        return swarm

    def distribute_tasks(self, swarm_id: str, *, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        swarm = self.get(swarm_id)
        fleet_ids = swarm["fleet_ids"]
        allocated = []
        for i, task in enumerate(tasks):
            allocated.append({**task, "assigned_to": fleet_ids[i % len(fleet_ids)]})
        swarm["tasks"] = allocated
        swarm["status"] = "tasks_allocated"
        self.store.swarm_missions.save(swarm_id, swarm)
        return swarm

    def area_coverage(self, swarm_id: str, *, bounds: dict[str, float], spacing_m: float = 50.0) -> dict[str, Any]:
        swarm = self.get(swarm_id)
        n = len(swarm["fleet_ids"])
        strips = []
        south, north = float(bounds["south"]), float(bounds["north"])
        west, east = float(bounds["west"]), float(bounds["east"])
        step = (north - south) / max(n, 1)
        for i, fid in enumerate(swarm["fleet_ids"]):
            strips.append(
                {
                    "fleet_id": fid,
                    "corridor": {"south": south + i * step, "north": south + (i + 1) * step, "west": west, "east": east},
                    "spacing_m": spacing_m,
                }
            )
        swarm["coverage"] = strips
        swarm["status"] = "area_coverage"
        self.store.swarm_missions.save(swarm_id, swarm)
        return swarm

    def automatic_recovery(self, swarm_id: str, *, failed_fleet_id: str) -> dict[str, Any]:
        swarm = self.get(swarm_id)
        remaining = [f for f in swarm["fleet_ids"] if f != failed_fleet_id]
        if not remaining:
            swarm["status"] = "aborted"
            swarm["health"] = "critical"
        else:
            if swarm.get("leader_id") == failed_fleet_id:
                swarm["leader_id"] = remaining[0]
                swarm["roles"] = [{"fleet_id": f, "role": "leader" if f == remaining[0] else "follower"} for f in remaining]
            swarm["fleet_ids"] = remaining
            swarm["recovery"] = {"failed": failed_fleet_id, "at": _now()}
            swarm["status"] = "recovered"
            swarm["health"] = "degraded"
        self.store.swarm_missions.save(swarm_id, swarm)
        return swarm

    def swarm_health(self, swarm_id: str, *, vehicle_health: dict[str, str] | None = None) -> dict[str, Any]:
        swarm = self.get(swarm_id)
        vehicle_health = dict(vehicle_health or {})
        unhealthy = [fid for fid in swarm["fleet_ids"] if vehicle_health.get(fid, "ok") != "ok"]
        health = "ok" if not unhealthy else "degraded" if len(unhealthy) < len(swarm["fleet_ids"]) else "critical"
        swarm["health"] = health
        swarm["unhealthy"] = unhealthy
        self.store.swarm_missions.save(swarm_id, swarm)
        return {"swarm_id": swarm_id, "health": health, "unhealthy": unhealthy}

    def decision_engine(self, swarm_id: str, *, observations: dict[str, Any] | None = None) -> dict[str, Any]:
        swarm = self.get(swarm_id)
        obs = dict(observations or {})
        decisions = []
        if obs.get("member_lost"):
            decisions.append({"action": "automatic_recovery", "reason": "member_lost"})
        if obs.get("coverage_gap"):
            decisions.append({"action": "redistribute_tasks", "reason": "coverage_gap"})
        if obs.get("low_battery_ids"):
            decisions.append({"action": "rtl_subset", "targets": obs["low_battery_ids"]})
        if not decisions:
            decisions.append({"action": "continue", "reason": "nominal"})
        result = {"swarm_id": swarm_id, "decisions": decisions, "primary": decisions[0], "formation": swarm.get("formation")}
        swarm["last_decision"] = result
        self.store.swarm_missions.save(swarm_id, swarm)
        return result

    def list(self) -> list[dict[str, Any]]:
        return self.store.swarm_missions.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "swarm_intelligence": "1.0",
            "swarm_count": self.store.swarm_missions.count(),
            "capabilities": [
                "multi_uav_missions",
                "formation_flight",
                "leader_follower",
                "distributed_tasks",
                "area_coverage",
                "dynamic_task_allocation",
                "target_distribution",
                "automatic_recovery",
                "swarm_health",
                "swarm_ai_decision_engine",
            ],
        }


swarm_intelligence = SwarmIntelligence()
