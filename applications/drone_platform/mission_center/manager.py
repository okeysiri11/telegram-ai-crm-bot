"""Mission Center — planning, scheduling, validation, replay (Sprint 11.7)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.missions.service import MissionService, mission_service
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MissionCenter:
    def __init__(self, store: DroneStore | None = None, missions: MissionService | None = None) -> None:
        self.store = store or drone_store
        self.missions = missions or mission_service

    def create_ops_mission(
        self,
        *,
        name: str,
        waypoints: list[dict[str, Any]] | None = None,
        template_id: str = "",
        scheduled_at: str = "",
        priority: str = "normal",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        mid = f"ops_{uuid.uuid4().hex[:12]}"
        # also keep a planning mission record
        plan = self.missions.create_mission(name=name, waypoints=waypoints or [], is_template=False)
        item = {
            "ops_mission_id": mid,
            "mission_id": plan.mission_id,
            "name": name,
            "template_id": template_id,
            "waypoints": list(waypoints or []),
            "status": "draft",
            "priority": priority,
            "scheduled_at": scheduled_at,
            "timeline": [{"event": "created", "at": _now()}],
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.ops_missions.save(mid, item)
        return item

    def get(self, ops_mission_id: str) -> dict[str, Any]:
        item = self.store.ops_missions.get(ops_mission_id)
        if item is None:
            raise NotFoundError("ops_mission", ops_mission_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.ops_missions.list_all()

    def create_template(self, *, name: str, waypoints: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        tmpl = self.missions.create_mission(name=name, waypoints=waypoints or [], is_template=True)
        return tmpl.to_dict()

    def list_templates(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self.missions.list_missions(templates_only=True)]

    def schedule(self, ops_mission_id: str, *, scheduled_at: str, window_min: int = 60) -> dict[str, Any]:
        mission = self.get(ops_mission_id)
        sid = f"sch_{uuid.uuid4().hex[:12]}"
        schedule = {
            "schedule_id": sid,
            "ops_mission_id": ops_mission_id,
            "scheduled_at": scheduled_at,
            "window_min": window_min,
            "status": "scheduled",
            "created_at": _now(),
        }
        self.store.mission_schedules.save(sid, schedule)
        mission["scheduled_at"] = scheduled_at
        mission["status"] = "scheduled"
        mission["timeline"].append({"event": "scheduled", "at": _now(), "schedule_id": sid})
        self.store.ops_missions.save(ops_mission_id, mission)
        return schedule

    def timeline(self, ops_mission_id: str) -> dict[str, Any]:
        mission = self.get(ops_mission_id)
        return {"ops_mission_id": ops_mission_id, "events": list(mission.get("timeline") or [])}

    def validate(self, ops_mission_id: str) -> dict[str, Any]:
        mission = self.get(ops_mission_id)
        issues = []
        if not mission.get("waypoints"):
            issues.append("No waypoints")
        for i, wp in enumerate(mission.get("waypoints") or []):
            if "lat" not in wp or "lon" not in wp:
                issues.append(f"Waypoint {i} missing lat/lon")
        result = {"ops_mission_id": ops_mission_id, "valid": not issues, "issues": issues}
        mission["timeline"].append({"event": "validated", "valid": result["valid"], "at": _now()})
        self.store.ops_missions.save(ops_mission_id, mission)
        return result

    def simulate(self, ops_mission_id: str, *, speed_mps: float = 12.0) -> dict[str, Any]:
        mission = self.get(ops_mission_id)
        wps = mission.get("waypoints") or []
        est_min = max(1.0, len(wps) * 0.5)
        sim = {
            "ops_mission_id": ops_mission_id,
            "waypoint_count": len(wps),
            "speed_mps": speed_mps,
            "estimated_min": round(est_min, 2),
            "status": "simulated",
            "at": _now(),
        }
        mission["last_simulation"] = sim
        mission["timeline"].append({"event": "simulated", "at": _now()})
        self.store.ops_missions.save(ops_mission_id, mission)
        return sim

    def replay(self, ops_mission_id: str) -> dict[str, Any]:
        mission = self.get(ops_mission_id)
        steps = [{"i": i, "waypoint": wp} for i, wp in enumerate(mission.get("waypoints") or [])]
        return {"ops_mission_id": ops_mission_id, "steps": steps, "step_count": len(steps)}

    def archive(self, ops_mission_id: str, *, reason: str = "completed") -> dict[str, Any]:
        mission = self.get(ops_mission_id)
        aid = f"arc_{uuid.uuid4().hex[:12]}"
        archive = {
            "archive_id": aid,
            "ops_mission_id": ops_mission_id,
            "snapshot": dict(mission),
            "reason": reason,
            "archived_at": _now(),
        }
        self.store.mission_archives.save(aid, archive)
        mission["status"] = "archived"
        mission["timeline"].append({"event": "archived", "at": _now()})
        self.store.ops_missions.save(ops_mission_id, mission)
        return archive

    def report(self, ops_mission_id: str, *, success: bool = True, notes: str = "") -> dict[str, Any]:
        mission = self.get(ops_mission_id)
        rid = f"mrep_{uuid.uuid4().hex[:12]}"
        report = {
            "report_id": rid,
            "ops_mission_id": ops_mission_id,
            "name": mission.get("name"),
            "success": success,
            "notes": notes,
            "waypoint_count": len(mission.get("waypoints") or []),
            "created_at": _now(),
        }
        self.store.mission_reports.save(rid, report)
        mission["timeline"].append({"event": "reported", "success": success, "at": _now()})
        self.store.ops_missions.save(ops_mission_id, mission)
        return report

    def update_status(self, ops_mission_id: str, status: str) -> dict[str, Any]:
        mission = self.get(ops_mission_id)
        mission["status"] = status
        mission["timeline"].append({"event": "status", "status": status, "at": _now()})
        self.store.ops_missions.save(ops_mission_id, mission)
        return mission

    def status(self) -> dict[str, Any]:
        return {
            "mission_center": "1.0",
            "ops_missions": self.store.ops_missions.count(),
            "schedules": self.store.mission_schedules.count(),
            "archives": self.store.mission_archives.count(),
            "reports": self.store.mission_reports.count(),
            "capabilities": [
                "mission_manager",
                "mission_planner",
                "mission_templates",
                "mission_scheduler",
                "mission_timeline",
                "mission_validator",
                "mission_simulator",
                "mission_replay",
                "mission_archive",
                "mission_reports",
            ],
        }


mission_center = MissionCenter()
