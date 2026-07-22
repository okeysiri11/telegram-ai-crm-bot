"""Mission AI — optimization and decision support (Sprint 11.7)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.production_ai import ProductionAIAssistant


MISSION_AI_CAPABILITIES = (
    "mission_optimization",
    "route_optimization",
    "battery_optimization",
    "risk_prediction",
    "obstacle_prediction",
    "weather_analysis",
    "mission_scoring",
    "mission_recommendations",
    "mission_validation_ai",
    "emergency_recommendations",
)


class MissionAIAssistant(ProductionAIAssistant):
    def capabilities(self) -> list[str]:
        return list(dict.fromkeys([*super().capabilities(), *MISSION_AI_CAPABILITIES]))

    def mission_optimization(self, *, waypoints: list[dict[str, Any]], goals: list[str] | None = None) -> dict[str, Any]:
        response = {
            "waypoint_count": len(waypoints),
            "goals": list(goals or ["coverage", "endurance"]),
            "suggestions": ["Remove near-duplicate waypoints", "Keep RTH reserve", "Align altitude with terrain clearance"],
        }
        return self._session(agent="mission_optimization", query="optimize", context={"goals": goals}, response=response)

    def route_optimization(self, *, start: dict[str, Any], goal: dict[str, Any], obstacles: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        response = {
            "start": start,
            "goal": goal,
            "obstacle_count": len(obstacles or []),
            "recommendation": "Use obstacle-aware corridor with mid-point climb if obstacles present",
        }
        return self._session(agent="route_optimization", query="route", context=response, response=response)

    def battery_optimization(self, *, battery_pct: float, distance_m: float) -> dict[str, Any]:
        ok = battery_pct >= 35 or distance_m < 1500
        response = {"battery_pct": battery_pct, "distance_m": distance_m, "sufficient": ok, "advice": "Proceed" if ok else "Reduce distance or swap battery"}
        return self._session(agent="battery_optimization", query="battery", context=response, response=response)

    def risk_prediction(self, *, wind_mps: float, gps_quality: str = "good", link_quality: str = "good") -> dict[str, Any]:
        score = 10 - (wind_mps / 2) - (2 if gps_quality != "good" else 0) - (2 if link_quality != "good" else 0)
        level = "low" if score >= 7 else "medium" if score >= 4 else "high"
        response = {"risk_score": round(max(0, score), 2), "risk_level": level, "wind_mps": wind_mps, "gps_quality": gps_quality, "link_quality": link_quality}
        return self._session(agent="risk_prediction", query="risk", context=response, response=response)

    def obstacle_prediction(self, *, detections: list[str] | None = None) -> dict[str, Any]:
        dets = list(detections or [])
        response = {"detections": dets, "predicted_conflicts": len(dets), "advice": "Replan laterally" if dets else "Path clear"}
        return self._session(agent="obstacle_prediction", query="obstacles", context={"detections": dets}, response=response)

    def weather_analysis(self, *, wind_mps: float, visibility_km: float, precip: bool = False) -> dict[str, Any]:
        flyable = wind_mps < 12 and visibility_km >= 2 and not precip
        response = {"wind_mps": wind_mps, "visibility_km": visibility_km, "precip": precip, "flyable": flyable}
        return self._session(agent="weather_analysis", query="weather", context=response, response=response)

    def mission_scoring(self, *, validation_ok: bool, risk_level: str, battery_ok: bool) -> dict[str, Any]:
        score = 100
        if not validation_ok:
            score -= 30
        if risk_level == "high":
            score -= 25
        elif risk_level == "medium":
            score -= 10
        if not battery_ok:
            score -= 20
        grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"
        response = {"score": max(0, score), "grade": grade}
        return self._session(agent="mission_scoring", query="score", context=response, response=response)

    def mission_recommendations(self, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {
            "context": dict(context or {}),
            "recommendations": [
                "Confirm fleet readiness and battery assignment",
                "Validate geofence and RTH point",
                "Brief operators on abort criteria",
            ],
        }
        return self._session(agent="mission_recommendations", query="recommend", context=dict(context or {}), response=response)

    def mission_validation_ai(self, *, issues: list[str] | None = None) -> dict[str, Any]:
        issues = list(issues or [])
        response = {"issues": issues, "valid": not issues, "guidance": "Fix listed issues before arming" if issues else "Mission structure looks valid"}
        return self._session(agent="mission_validation_ai", query="validate", context={"issues": issues}, response=response)

    def emergency_recommendations(self, *, emergency_type: str) -> dict[str, Any]:
        response = {
            "emergency_type": emergency_type,
            "recommendations": ["Notify mission commander", "Execute failsafe policy", "Preserve logs for post-flight analysis"],
            "policy": "engineering_assistance_only",
        }
        return self._session(agent="emergency_recommendations", query=emergency_type, context=response, response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        key = agent.lower().replace("-", "_")
        dispatch = {
            "mission_optimization": lambda: self.mission_optimization(waypoints=ctx.get("waypoints") or [], goals=ctx.get("goals")),
            "route_optimization": lambda: self.route_optimization(start=ctx.get("start") or {}, goal=ctx.get("goal") or {}, obstacles=ctx.get("obstacles")),
            "battery_optimization": lambda: self.battery_optimization(battery_pct=float(ctx.get("battery_pct", 80)), distance_m=float(ctx.get("distance_m", 1000))),
            "risk_prediction": lambda: self.risk_prediction(wind_mps=float(ctx.get("wind_mps", 5)), gps_quality=ctx.get("gps_quality", "good"), link_quality=ctx.get("link_quality", "good")),
            "obstacle_prediction": lambda: self.obstacle_prediction(detections=ctx.get("detections") or [query] if query else []),
            "weather_analysis": lambda: self.weather_analysis(wind_mps=float(ctx.get("wind_mps", 4)), visibility_km=float(ctx.get("visibility_km", 8)), precip=bool(ctx.get("precip", False))),
            "mission_scoring": lambda: self.mission_scoring(validation_ok=bool(ctx.get("validation_ok", True)), risk_level=ctx.get("risk_level", "low"), battery_ok=bool(ctx.get("battery_ok", True))),
            "mission_recommendations": lambda: self.mission_recommendations(context=ctx),
            "mission_validation_ai": lambda: self.mission_validation_ai(issues=ctx.get("issues") or []),
            "emergency_recommendations": lambda: self.emergency_recommendations(emergency_type=query or ctx.get("emergency_type", "mission_abort")),
        }
        if key in dispatch:
            return dispatch[key]()
        return super().assist(agent=agent, query=query, context=context)


from applications.drone_platform.shared.store import drone_store

mission_ai = MissionAIAssistant(store=drone_store)
