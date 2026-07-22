"""Navigation AI — visual/GPS/denied, terrain, avoidance, planning (Sprint 11.4)."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class NavigationEngine:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def _save_plan(self, plan_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        pid = f"nav_{uuid.uuid4().hex[:12]}"
        plan = {"plan_id": pid, "plan_type": plan_type, "created_at": _now(), **payload}
        self.store.navigation_plans.save(pid, plan)
        return plan

    def visual_navigation(self, *, landmarks: list[dict[str, Any]], current: dict[str, float]) -> dict[str, Any]:
        return self._save_plan(
            "visual_navigation",
            {
                "mode": "visual",
                "landmarks": landmarks,
                "current": current,
                "fix": "visual_odometry",
                "status": "tracking",
            },
        )

    def gps_assisted(self, *, waypoints: list[dict[str, Any]], gps_ok: bool = True) -> dict[str, Any]:
        return self._save_plan(
            "gps_assisted",
            {
                "mode": "gps_assisted",
                "waypoints": waypoints,
                "gps_ok": gps_ok,
                "status": "ready" if gps_ok else "degraded",
            },
        )

    def gps_denied(self, *, visual_fix: bool = True, imu_ok: bool = True) -> dict[str, Any]:
        status = "ready" if visual_fix and imu_ok else "unsafe"
        return self._save_plan(
            "gps_denied",
            {
                "mode": "gps_denied",
                "visual_fix": visual_fix,
                "imu_ok": imu_ok,
                "status": status,
                "strategy": ["visual_slam", "imu_dead_reckoning", "reduce_speed"],
            },
        )

    def terrain_following(self, *, clearance_m: float = 30.0, terrain_profile: list[float] | None = None) -> dict[str, Any]:
        profile = list(terrain_profile or [10, 12, 15, 11, 9])
        altitudes = [h + clearance_m for h in profile]
        return self._save_plan(
            "terrain_following",
            {"clearance_m": clearance_m, "terrain_profile": profile, "commanded_altitudes_m": altitudes},
        )

    def terrain_avoidance(self, *, obstacles: list[dict[str, Any]], altitude_m: float) -> dict[str, Any]:
        threats = [o for o in obstacles if float(o.get("height_m", 0)) + 5 >= altitude_m]
        return self._save_plan(
            "terrain_avoidance",
            {
                "altitude_m": altitude_m,
                "threat_count": len(threats),
                "threats": threats,
                "action": "climb" if threats else "continue",
                "recommended_alt_m": altitude_m + 20 if threats else altitude_m,
            },
        )

    def obstacle_avoidance(self, *, obstacles: list[dict[str, Any]], heading_deg: float = 0.0) -> dict[str, Any]:
        nearest = None
        if obstacles:
            nearest = min(obstacles, key=lambda o: float(o.get("distance_m", 1e9)))
        avoid = nearest is not None and float(nearest.get("distance_m", 1e9)) < 25
        return self._save_plan(
            "obstacle_avoidance",
            {
                "heading_deg": heading_deg,
                "nearest": nearest,
                "avoid": avoid,
                "maneuver": {"yaw_offset_deg": 30 if avoid else 0, "climb_m": 5 if avoid else 0},
            },
        )

    def dynamic_path_planning(
        self,
        *,
        start: dict[str, float],
        goal: dict[str, float],
        obstacles: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        mid = {
            "lat": (float(start["lat"]) + float(goal["lat"])) / 2,
            "lon": (float(start["lon"]) + float(goal["lon"])) / 2,
            "alt": max(float(start.get("alt", 40)), float(goal.get("alt", 40))) + (10 if obstacles else 0),
        }
        path = [start, mid, goal]
        distance = _haversine_m(float(start["lat"]), float(start["lon"]), float(goal["lat"]), float(goal["lon"]))
        return self._save_plan(
            "dynamic_path",
            {"path": path, "distance_m": round(distance, 1), "obstacle_count": len(obstacles or []), "status": "planned"},
        )

    def safe_landing_finder(self, *, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        if not candidates:
            raise ValidationError("landing candidates required")
        scored = []
        for c in candidates:
            score = float(c.get("flatness", 0.5)) * 40 + float(c.get("clearance", 0.5)) * 40 + float(c.get("confidence", 0.5)) * 20
            scored.append({**c, "score": round(score, 2)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return self._save_plan("safe_landing", {"candidates": scored, "primary": scored[0]})

    def route_optimizer(self, *, waypoints: list[dict[str, Any]]) -> dict[str, Any]:
        if len(waypoints) <= 2:
            return self._save_plan("route_optimizer", {"optimized": waypoints, "saved_m": 0})
        # keep ends, drop near-duplicates
        optimized = [waypoints[0]]
        for wp in waypoints[1:-1]:
            prev = optimized[-1]
            if _haversine_m(float(prev["lat"]), float(prev["lon"]), float(wp["lat"]), float(wp["lon"])) >= 3:
                optimized.append(wp)
        optimized.append(waypoints[-1])
        before = sum(
            _haversine_m(float(waypoints[i]["lat"]), float(waypoints[i]["lon"]), float(waypoints[i + 1]["lat"]), float(waypoints[i + 1]["lon"]))
            for i in range(len(waypoints) - 1)
        )
        after = sum(
            _haversine_m(float(optimized[i]["lat"]), float(optimized[i]["lon"]), float(optimized[i + 1]["lat"]), float(optimized[i + 1]["lon"]))
            for i in range(len(optimized) - 1)
        )
        return self._save_plan(
            "route_optimizer",
            {"optimized": optimized, "saved_m": round(max(0, before - after), 1), "waypoint_count": len(optimized)},
        )

    def emergency_route(self, *, current: dict[str, float], home: dict[str, float], battery_pct: float) -> dict[str, Any]:
        distance = _haversine_m(float(current["lat"]), float(current["lon"]), float(home["lat"]), float(home["lon"]))
        viable = battery_pct >= 20 and distance < 3000
        return self._save_plan(
            "emergency_route",
            {
                "current": current,
                "home": home,
                "distance_m": round(distance, 1),
                "battery_pct": battery_pct,
                "rth_viable": viable,
                "route": [current, home] if viable else [current],
                "action": "rth" if viable else "land_immediate",
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "navigation_ai": "1.0",
            "plan_count": self.store.navigation_plans.count(),
            "capabilities": [
                "navigation_engine",
                "visual_navigation",
                "gps_assisted",
                "gps_denied",
                "terrain_following",
                "terrain_avoidance",
                "obstacle_avoidance",
                "dynamic_path_planning",
                "safe_landing_finder",
                "route_optimizer",
                "emergency_route_planner",
            ],
        }


navigation_engine = NavigationEngine()
