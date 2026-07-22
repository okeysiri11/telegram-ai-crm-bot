"""Mission Intelligence — validation, optimization, risk, predictions (Sprint 11.3)."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.missions.service import MissionService, mission_service
from applications.drone_platform.models.missions import Mission
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
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


def _path_distance(waypoints: list[dict[str, Any]]) -> float:
    total = 0.0
    prev = None
    for wp in waypoints:
        if "lat" not in wp or "lon" not in wp:
            continue
        cur = (float(wp["lat"]), float(wp["lon"]))
        if prev is not None:
            total += _haversine_m(prev[0], prev[1], cur[0], cur[1])
        prev = cur
    return total


class MissionValidator:
    def validate(self, mission: Mission) -> dict[str, Any]:
        issues: list[str] = []
        if not mission.waypoints:
            issues.append("Mission has no waypoints")
        for i, wp in enumerate(mission.waypoints):
            if "lat" not in wp or "lon" not in wp:
                issues.append(f"Waypoint {i} missing lat/lon")
            alt = wp.get("alt", wp.get("z"))
            if alt is not None and float(alt) < 0:
                issues.append(f"Waypoint {i} has negative altitude")
        if mission.geofences:
            for g in mission.geofences:
                if not g.get("polygon") and not g.get("radius"):
                    issues.append("Geofence missing geometry")
        return {"valid": not issues, "issues": issues, "waypoint_count": len(mission.waypoints)}


class WaypointOptimizer:
    def optimize(self, waypoints: list[dict[str, Any]]) -> dict[str, Any]:
        if len(waypoints) <= 2:
            return {"optimized": list(waypoints), "removed": 0, "note": "Nothing to optimize"}
        optimized = [waypoints[0]]
        removed = 0
        for wp in waypoints[1:-1]:
            prev, nxt = optimized[-1], waypoints[waypoints.index(wp) + 1] if wp in waypoints else waypoints[-1]
            # drop near-duplicates
            if "lat" in wp and "lat" in prev:
                if _haversine_m(float(prev["lat"]), float(prev["lon"]), float(wp["lat"]), float(wp["lon"])) < 2.0:
                    removed += 1
                    continue
            optimized.append(wp)
        optimized.append(waypoints[-1])
        return {
            "optimized": optimized,
            "removed": removed,
            "original_distance_m": _path_distance(waypoints),
            "optimized_distance_m": _path_distance(optimized),
        }


class TerrainAnalyzer:
    def analyze(self, waypoints: list[dict[str, Any]], *, terrain_clearance_m: float = 30.0) -> dict[str, Any]:
        alts = [float(wp.get("alt", wp.get("z", 0)) or 0) for wp in waypoints]
        min_alt = min(alts) if alts else None
        return {
            "min_altitude_m": min_alt,
            "max_altitude_m": max(alts) if alts else None,
            "clearance_ok": min_alt is None or min_alt >= terrain_clearance_m,
            "terrain_clearance_m": terrain_clearance_m,
        }


class FlightRiskEstimator:
    def estimate(self, *, distance_m: float, battery_pct: float, wind_mps: float = 0.0, issues: list[str] | None = None) -> dict[str, Any]:
        score = 10.0
        score -= min(distance_m / 1000.0, 5)
        score -= max(0, (40 - battery_pct) / 10)
        score -= wind_mps / 5
        score -= len(issues or []) * 0.5
        score = max(0.0, min(10.0, score))
        level = "low" if score >= 7 else "medium" if score >= 4 else "high"
        return {"risk_score": round(score, 2), "risk_level": level, "factors": {"distance_m": distance_m, "battery_pct": battery_pct, "wind_mps": wind_mps, "issues": issues or []}}


class BatteryPrediction:
    def predict(self, *, distance_m: float, cruise_speed_mps: float = 12.0, drain_pct_per_min: float = 2.5, start_pct: float = 100.0) -> dict[str, Any]:
        minutes = (distance_m / max(cruise_speed_mps, 0.1)) / 60.0
        used = minutes * drain_pct_per_min
        remaining = start_pct - used
        return {
            "estimated_flight_min": round(minutes, 2),
            "estimated_drain_pct": round(used, 2),
            "estimated_remaining_pct": round(remaining, 2),
            "sufficient": remaining >= 25,
        }


class RangePrediction:
    def predict(self, *, battery_pct: float, drain_pct_per_km: float = 8.0) -> dict[str, Any]:
        usable = max(0.0, battery_pct - 25.0)
        range_km = usable / max(drain_pct_per_km, 0.1)
        return {"usable_battery_pct": usable, "estimated_range_km": round(range_km, 2), "reserve_pct": 25.0}


class ReturnToHomeSimulator:
    def simulate(self, *, home: dict[str, float], current: dict[str, float], battery_pct: float) -> dict[str, Any]:
        distance = _haversine_m(float(home["lat"]), float(home["lon"]), float(current["lat"]), float(current["lon"]))
        batt = BatteryPrediction().predict(distance_m=distance, start_pct=battery_pct)
        return {
            "distance_m": round(distance, 1),
            "battery": batt,
            "rth_viable": batt["sufficient"],
            "recommendation": "RTH OK" if batt["sufficient"] else "Land nearby / reduce distance",
        }


class EmergencyLandingSuggestions:
    def suggest(self, *, current: dict[str, float], rally_points: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        candidates = []
        for rp in rally_points or []:
            if "lat" not in rp or "lon" not in rp:
                continue
            d = _haversine_m(float(current["lat"]), float(current["lon"]), float(rp["lat"]), float(rp["lon"]))
            candidates.append({"point": rp, "distance_m": round(d, 1)})
        candidates.sort(key=lambda c: c["distance_m"])
        if not candidates:
            candidates = [{"point": {"lat": current["lat"], "lon": current["lon"], "note": "current position"}, "distance_m": 0.0}]
        return {"suggestions": candidates[:5], "primary": candidates[0]}


class MissionReplay:
    def replay(self, mission: Mission) -> dict[str, Any]:
        steps = []
        for i, wp in enumerate(mission.waypoints):
            steps.append({"step": i, "waypoint": wp, "action": "navigate"})
        return {"mission_id": mission.mission_id, "steps": steps, "step_count": len(steps)}


class MissionComparison:
    def compare(self, left: Mission, right: Mission) -> dict[str, Any]:
        return {
            "left_id": left.mission_id,
            "right_id": right.mission_id,
            "waypoint_delta": len(right.waypoints) - len(left.waypoints),
            "distance_left_m": _path_distance(left.waypoints),
            "distance_right_m": _path_distance(right.waypoints),
            "same_uav": left.uav_id == right.uav_id,
        }


class MissionScoring:
    def score(self, *, validation: dict[str, Any], risk: dict[str, Any], battery: dict[str, Any], terrain: dict[str, Any]) -> dict[str, Any]:
        score = 100
        score -= 15 * len(validation.get("issues") or [])
        if risk.get("risk_level") == "high":
            score -= 25
        elif risk.get("risk_level") == "medium":
            score -= 10
        if not battery.get("sufficient", True):
            score -= 20
        if not terrain.get("clearance_ok", True):
            score -= 15
        score = max(0, min(100, score))
        grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"
        return {"score": score, "grade": grade}


class MissionIntelligenceManager:
    def __init__(self, store: DroneStore | None = None, missions: MissionService | None = None) -> None:
        self.store = store or drone_store
        self.missions = missions or mission_service
        self.validator = MissionValidator()
        self.optimizer = WaypointOptimizer()
        self.terrain = TerrainAnalyzer()
        self.risk = FlightRiskEstimator()
        self.battery = BatteryPrediction()
        self.range = RangePrediction()
        self.rth = ReturnToHomeSimulator()
        self.emergency = EmergencyLandingSuggestions()
        self.replay = MissionReplay()
        self.comparison = MissionComparison()
        self.scoring = MissionScoring()

    def analyze_mission(
        self,
        mission_id: str,
        *,
        battery_pct: float = 100.0,
        wind_mps: float = 0.0,
        cruise_speed_mps: float = 12.0,
    ) -> dict[str, Any]:
        mission = self.missions.get_mission(mission_id)
        validation = self.validator.validate(mission)
        distance = _path_distance(mission.waypoints)
        terrain = self.terrain.analyze(mission.waypoints)
        battery = self.battery.predict(distance_m=distance, cruise_speed_mps=cruise_speed_mps, start_pct=battery_pct)
        risk = self.risk.estimate(distance_m=distance, battery_pct=battery_pct, wind_mps=wind_mps, issues=validation["issues"])
        optimized = self.optimizer.optimize(mission.waypoints)
        score = self.scoring.score(validation=validation, risk=risk, battery=battery, terrain=terrain)
        aid = f"man_{uuid.uuid4().hex[:12]}"
        report = {
            "analysis_id": aid,
            "mission_id": mission_id,
            "validation": validation,
            "distance_m": round(distance, 1),
            "terrain": terrain,
            "battery": battery,
            "range": self.range.predict(battery_pct=battery_pct),
            "risk": risk,
            "optimization": optimized,
            "replay": self.replay.replay(mission),
            "score": score,
            "created_at": _now(),
        }
        self.store.mission_analyses.save(aid, report)
        return report

    def compare_missions(self, left_id: str, right_id: str) -> dict[str, Any]:
        left = self.missions.get_mission(left_id)
        right = self.missions.get_mission(right_id)
        return self.comparison.compare(left, right)

    def simulate_rth(self, *, home: dict[str, float], current: dict[str, float], battery_pct: float) -> dict[str, Any]:
        return self.rth.simulate(home=home, current=current, battery_pct=battery_pct)

    def emergency_landing(self, mission_id: str, current: dict[str, float]) -> dict[str, Any]:
        mission = self.missions.get_mission(mission_id)
        return self.emergency.suggest(current=current, rally_points=mission.rally_points)

    def status(self) -> dict[str, Any]:
        return {
            "mission_intelligence": "1.0",
            "analysis_count": self.store.mission_analyses.count(),
            "capabilities": [
                "validator",
                "waypoint_optimizer",
                "terrain_analyzer",
                "flight_risk_estimator",
                "battery_prediction",
                "range_prediction",
                "rth_simulator",
                "emergency_landing",
                "mission_replay",
                "mission_comparison",
                "mission_scoring",
            ],
        }


mission_intelligence = MissionIntelligenceManager()
