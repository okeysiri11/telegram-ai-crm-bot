"""Autonomous flight modes and decision engine (Sprint 11.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutonomyEngine:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def _save(self, mode: str, payload: dict[str, Any]) -> dict[str, Any]:
        aid = f"auto_{uuid.uuid4().hex[:12]}"
        item = {"autonomy_id": aid, "mode": mode, "created_at": _now(), "status": "active", **payload}
        self.store.autonomy_missions.save(aid, item)
        return item

    def takeoff_assistant(self, *, target_alt_m: float = 10.0, clear: bool = True) -> dict[str, Any]:
        return self._save(
            "takeoff",
            {
                "target_alt_m": target_alt_m,
                "clear": clear,
                "checklist": ["motors_spinning", "climb_rate_ok", "attitude_stable"],
                "go": clear,
            },
        )

    def landing_assistant(self, *, zone: dict[str, Any], battery_pct: float = 50.0) -> dict[str, Any]:
        return self._save(
            "landing",
            {
                "zone": zone,
                "battery_pct": battery_pct,
                "descent_rate_mps": 1.0,
                "abort_if_obstacle": True,
                "go": bool(zone),
            },
        )

    def autonomous_patrol(self, *, waypoints: list[dict[str, Any]], loops: int = 1) -> dict[str, Any]:
        if not waypoints:
            raise ValidationError("patrol waypoints required")
        return self._save("patrol", {"waypoints": waypoints, "loops": loops, "progress": 0})

    def waypoint_ai(self, *, waypoints: list[dict[str, Any]], adapt: bool = True) -> dict[str, Any]:
        return self._save(
            "waypoint_ai",
            {
                "waypoints": waypoints,
                "adapt": adapt,
                "policies": ["slow_near_obstacles", "hold_on_link_loss", "skip_unreachable"],
            },
        )

    def target_following(self, *, track_id: str, standoff_m: float = 15.0) -> dict[str, Any]:
        return self._save("target_following", {"track_id": track_id, "standoff_m": standoff_m})

    def orbit_mode(self, *, center: dict[str, float], radius_m: float = 50.0, speed_mps: float = 5.0) -> dict[str, Any]:
        return self._save("orbit", {"center": center, "radius_m": radius_m, "speed_mps": speed_mps})

    def search_pattern(self, *, bounds: dict[str, float], pattern: str = "lawnmower", spacing_m: float = 40.0) -> dict[str, Any]:
        south, north = float(bounds["south"]), float(bounds["north"])
        west, east = float(bounds["west"]), float(bounds["east"])
        waypoints = []
        lat = south
        row = 0
        # coarse grid in degrees (~111km per deg)
        step = spacing_m / 111000.0
        while lat <= north:
            if row % 2 == 0:
                waypoints.append({"lat": lat, "lon": west})
                waypoints.append({"lat": lat, "lon": east})
            else:
                waypoints.append({"lat": lat, "lon": east})
                waypoints.append({"lat": lat, "lon": west})
            lat += step
            row += 1
        return self._save("search_pattern", {"pattern": pattern, "spacing_m": spacing_m, "waypoints": waypoints, "count": len(waypoints)})

    def area_coverage(self, *, bounds: dict[str, float], altitude_m: float = 60.0, overlap: float = 0.3) -> dict[str, Any]:
        pattern = self.search_pattern(bounds=bounds, spacing_m=40 * (1 - overlap))
        return self._save(
            "area_coverage",
            {
                "bounds": bounds,
                "altitude_m": altitude_m,
                "overlap": overlap,
                "waypoints": pattern["waypoints"],
                "search_ref": pattern["autonomy_id"],
            },
        )

    def swarm_ready(self, *, vehicle_ids: list[str], formation: str = "line") -> dict[str, Any]:
        return self._save(
            "swarm",
            {
                "architecture_ready": True,
                "vehicle_ids": list(vehicle_ids),
                "formation": formation,
                "roles": [{"vehicle_id": v, "role": "follower" if i else "leader"} for i, v in enumerate(vehicle_ids)],
            },
        )

    def decision_engine(
        self,
        *,
        observations: dict[str, Any],
        battery_pct: float = 100.0,
        link_ok: bool = True,
    ) -> dict[str, Any]:
        decisions = []
        if battery_pct < 25:
            decisions.append({"action": "rth_or_land", "reason": "low_battery"})
        if not link_ok:
            decisions.append({"action": "failsafe_hold", "reason": "link_loss"})
        if observations.get("obstacle_near"):
            decisions.append({"action": "avoid", "reason": "obstacle"})
        if observations.get("unsafe_landing"):
            decisions.append({"action": "reselect_lz", "reason": "unsafe_lz"})
        if not decisions:
            decisions.append({"action": "continue_mission", "reason": "nominal"})
        return self._save(
            "decision",
            {
                "observations": observations,
                "battery_pct": battery_pct,
                "link_ok": link_ok,
                "decisions": decisions,
                "primary": decisions[0],
            },
        )

    def get(self, autonomy_id: str) -> dict[str, Any]:
        item = self.store.autonomy_missions.get(autonomy_id)
        if item is None:
            raise NotFoundError("autonomy_mission", autonomy_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.autonomy_missions.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "autonomous_flight": "1.0",
            "mission_count": self.store.autonomy_missions.count(),
            "swarm_architecture_ready": True,
            "capabilities": [
                "takeoff_assistant",
                "landing_assistant",
                "autonomous_patrol",
                "waypoint_ai",
                "target_following",
                "orbit_mode",
                "search_pattern",
                "area_coverage",
                "swarm_ready",
                "decision_engine",
            ],
        }


autonomy_engine = AutonomyEngine()
