"""AI Flight Assistant — vision/navigation/autonomy recommendations (Sprint 11.4)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.telemetry_ai import TelemetryFlightAIAssistant


VISION_FLIGHT_AI_CAPABILITIES = (
    "recommend_flight_path",
    "detect_unsafe_conditions",
    "predict_mission_success",
    "estimate_remaining_battery",
    "suggest_alternate_landing_zones",
    "optimize_camera_angles",
    "optimize_flight_altitude",
    "optimize_speed",
    "optimize_mission_timing",
)


class VisionFlightAIAssistant(TelemetryFlightAIAssistant):
    """Extends telemetry AI with vision, navigation, and autonomy assistance."""

    def capabilities(self) -> list[str]:
        return list(dict.fromkeys([*super().capabilities(), *VISION_FLIGHT_AI_CAPABILITIES]))

    def recommend_flight_path(self, *, start: dict[str, Any], goal: dict[str, Any], constraints: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {
            "start": start,
            "goal": goal,
            "constraints": dict(constraints or {}),
            "recommendation": "Prefer obstacle-aware corridor with terrain clearance margin and RTH reserve.",
            "suggested_alt_m": float((constraints or {}).get("alt_m", 50)),
        }
        return self._session(agent="recommend_flight_path", query="path", context={"start": start, "goal": goal}, response=response)

    def detect_unsafe_conditions(self, *, observations: dict[str, Any]) -> dict[str, Any]:
        flags = []
        if observations.get("wind_mps", 0) > 12:
            flags.append("high_wind")
        if observations.get("battery_pct", 100) < 25:
            flags.append("low_battery")
        if observations.get("obstacle_near"):
            flags.append("obstacle")
        if observations.get("gps_denied") and not observations.get("visual_fix"):
            flags.append("nav_degraded")
        response = {
            "observations": observations,
            "unsafe": bool(flags),
            "flags": flags,
            "advice": "Abort or replan" if flags else "Conditions acceptable for continued flight",
        }
        return self._session(agent="detect_unsafe_conditions", query="safety", context=observations, response=response)

    def predict_mission_success(self, *, risk_score: float, battery_ok: bool, weather_ok: bool) -> dict[str, Any]:
        p = 0.9
        if risk_score < 5:
            p -= 0.25
        if not battery_ok:
            p -= 0.3
        if not weather_ok:
            p -= 0.2
        p = max(0.05, min(0.99, p))
        response = {"probability": round(p, 2), "risk_score": risk_score, "battery_ok": battery_ok, "weather_ok": weather_ok}
        return self._session(agent="predict_mission_success", query="success", context=response, response=response)

    def estimate_remaining_battery(self, *, battery_pct: float, drain_pct_per_min: float, minutes_remaining_path: float) -> dict[str, Any]:
        used = drain_pct_per_min * minutes_remaining_path
        remaining = battery_pct - used
        response = {
            "estimated_remaining_pct": round(remaining, 2),
            "sufficient_with_reserve": remaining >= 25,
            "inputs": {"battery_pct": battery_pct, "drain_pct_per_min": drain_pct_per_min, "minutes_remaining_path": minutes_remaining_path},
        }
        return self._session(agent="estimate_remaining_battery", query="battery", context=response["inputs"], response=response)

    def suggest_alternate_landing_zones(self, *, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        ranked = sorted(candidates, key=lambda c: float(c.get("score", 0)), reverse=True)
        response = {"ranked": ranked, "primary": ranked[0] if ranked else None}
        return self._session(agent="suggest_alternate_landing_zones", query="lz", context={"count": len(candidates)}, response=response)

    def optimize_camera_angles(self, *, target: dict[str, Any], current_gimbal: dict[str, float] | None = None) -> dict[str, Any]:
        response = {
            "target": target,
            "current_gimbal": dict(current_gimbal or {}),
            "suggested": {"pitch_deg": -45, "yaw_offset_deg": 0, "zoom": 1.0},
        }
        return self._session(agent="optimize_camera_angles", query="camera", context=target, response=response)

    def optimize_flight_altitude(self, *, terrain_clearance_m: float, obstacles_max_m: float) -> dict[str, Any]:
        alt = max(terrain_clearance_m, obstacles_max_m + 15)
        response = {"recommended_alt_m": alt, "terrain_clearance_m": terrain_clearance_m, "obstacles_max_m": obstacles_max_m}
        return self._session(agent="optimize_flight_altitude", query="altitude", context=response, response=response)

    def optimize_speed(self, *, mode: str = "survey", wind_mps: float = 0.0) -> dict[str, Any]:
        base = {"survey": 8.0, "transit": 14.0, "tracking": 6.0}.get(mode, 10.0)
        speed = max(3.0, base - wind_mps * 0.3)
        response = {"mode": mode, "recommended_speed_mps": round(speed, 2), "wind_mps": wind_mps}
        return self._session(agent="optimize_speed", query=mode, context=response, response=response)

    def optimize_mission_timing(self, *, daylight_hours: float, battery_flights: int, priority: str = "coverage") -> dict[str, Any]:
        response = {
            "daylight_hours": daylight_hours,
            "battery_flights": battery_flights,
            "priority": priority,
            "suggested_windows": ["morning_calm", "midday_light"] if priority == "coverage" else ["shortest_path"],
        }
        return self._session(agent="optimize_mission_timing", query=priority, context=response, response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        agent_key = agent.lower().replace("-", "_")
        dispatch = {
            "recommend_flight_path": lambda: self.recommend_flight_path(
                start=ctx.get("start", {}), goal=ctx.get("goal", {}), constraints=ctx.get("constraints")
            ),
            "detect_unsafe_conditions": lambda: self.detect_unsafe_conditions(observations=ctx.get("observations") or {"note": query}),
            "predict_mission_success": lambda: self.predict_mission_success(
                risk_score=float(ctx.get("risk_score", 7)),
                battery_ok=bool(ctx.get("battery_ok", True)),
                weather_ok=bool(ctx.get("weather_ok", True)),
            ),
            "estimate_remaining_battery": lambda: self.estimate_remaining_battery(
                battery_pct=float(ctx.get("battery_pct", 80)),
                drain_pct_per_min=float(ctx.get("drain_pct_per_min", 2.5)),
                minutes_remaining_path=float(ctx.get("minutes_remaining_path", 10)),
            ),
            "suggest_alternate_landing_zones": lambda: self.suggest_alternate_landing_zones(candidates=ctx.get("candidates") or []),
            "optimize_camera_angles": lambda: self.optimize_camera_angles(target=ctx.get("target") or {"query": query}, current_gimbal=ctx.get("gimbal")),
            "optimize_flight_altitude": lambda: self.optimize_flight_altitude(
                terrain_clearance_m=float(ctx.get("terrain_clearance_m", 30)),
                obstacles_max_m=float(ctx.get("obstacles_max_m", 20)),
            ),
            "optimize_speed": lambda: self.optimize_speed(mode=ctx.get("mode", query or "survey"), wind_mps=float(ctx.get("wind_mps", 0))),
            "optimize_mission_timing": lambda: self.optimize_mission_timing(
                daylight_hours=float(ctx.get("daylight_hours", 8)),
                battery_flights=int(ctx.get("battery_flights", 3)),
                priority=ctx.get("priority", "coverage"),
            ),
        }
        if agent_key in dispatch:
            return dispatch[agent_key]()
        return super().assist(agent=agent, query=query, context=context)


from applications.drone_platform.shared.store import drone_store

vision_flight_ai = VisionFlightAIAssistant(store=drone_store)
