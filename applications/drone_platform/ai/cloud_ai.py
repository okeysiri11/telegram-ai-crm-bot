"""AI Command Center — fleet monitoring, predictions, optimization (Sprint 11.8)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.mission_ai import MissionAIAssistant


CLOUD_AI_CAPABILITIES = (
    "monitor_all_aircraft",
    "predict_failures",
    "predict_maintenance",
    "recommend_operators",
    "optimize_missions_cloud",
    "optimize_fleet_usage",
    "detect_anomalies_cloud",
    "generate_cloud_reports",
    "recommend_firmware_updates",
    "recommend_battery_replacements",
)


class CloudAIAssistant(MissionAIAssistant):
    def capabilities(self) -> list[str]:
        return list(dict.fromkeys([*super().capabilities(), *CLOUD_AI_CAPABILITIES]))

    def monitor_all_aircraft(self, *, aircraft: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        fleet = list(aircraft or [])
        unhealthy = [a for a in fleet if float(a.get("health", 1.0)) < 0.7]
        response = {"monitored": len(fleet), "attention": unhealthy, "status": "nominal" if not unhealthy else "attention"}
        return self._session(agent="monitor_all_aircraft", query="monitor", context={"count": len(fleet)}, response=response)

    def predict_failures(self, *, telemetry: dict[str, Any] | None = None) -> dict[str, Any]:
        t = dict(telemetry or {})
        vib = float(t.get("vibration", 0.2))
        temp = float(t.get("esc_temp_c", 40))
        risk = "high" if vib > 0.8 or temp > 85 else "medium" if vib > 0.5 or temp > 70 else "low"
        response = {"failure_risk": risk, "drivers": {"vibration": vib, "esc_temp_c": temp}, "advice": "Inspect motors" if risk != "low" else "Continue monitoring"}
        return self._session(agent="predict_failures", query="failures", context=t, response=response)

    def predict_maintenance(self, *, flight_hours: float = 0, cycles: int = 0) -> dict[str, Any]:
        due = flight_hours >= 40 or cycles >= 80
        response = {"flight_hours": flight_hours, "cycles": cycles, "maintenance_due": due, "window_h": max(0, 50 - flight_hours)}
        return self._session(agent="predict_maintenance", query="maintenance", context=response, response=response)

    def recommend_operators(self, *, mission_type: str = "survey", candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        cands = list(candidates or [])
        ranked = sorted(cands, key=lambda c: float(c.get("score", 0)), reverse=True)
        response = {"mission_type": mission_type, "recommended": ranked[:3], "policy": "engineering_assistance_only"}
        return self._session(agent="recommend_operators", query=mission_type, context={"candidates": len(cands)}, response=response)

    def optimize_missions_cloud(self, *, missions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        missions = list(missions or [])
        response = {
            "mission_count": len(missions),
            "suggestions": ["Batch nearby missions", "Prefer high-availability fleets", "Reserve RTH margin globally"],
        }
        return self._session(agent="optimize_missions_cloud", query="optimize", context={"count": len(missions)}, response=response)

    def optimize_fleet_usage(self, *, fleets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        fleets = list(fleets or [])
        idle = [f for f in fleets if f.get("availability") == "available"]
        response = {"fleets": len(fleets), "idle": len(idle), "advice": "Rebalance assignments toward idle fleets" if idle else "All fleets busy"}
        return self._session(agent="optimize_fleet_usage", query="fleet", context=response, response=response)

    def detect_anomalies_cloud(self, *, samples: list[float] | None = None) -> dict[str, Any]:
        samples = list(samples or [])
        mean = sum(samples) / len(samples) if samples else 0.0
        anomalies = [s for s in samples if abs(s - mean) > max(1.0, abs(mean) * 0.5)]
        response = {"sample_count": len(samples), "anomaly_count": len(anomalies), "anomalies": anomalies[:10]}
        return self._session(agent="detect_anomalies_cloud", query="anomalies", context=response, response=response)

    def generate_cloud_reports(self, *, period: str = "daily") -> dict[str, Any]:
        response = {
            "period": period,
            "sections": ["fleet_utilization", "mission_success", "incidents", "maintenance", "security_audit"],
            "status": "generated",
        }
        return self._session(agent="generate_cloud_reports", query=period, context=response, response=response)

    def recommend_firmware_updates(self, *, current: str = "", available: str = "") -> dict[str, Any]:
        recommend = bool(available) and available != current
        response = {"current": current, "available": available, "recommend_update": recommend, "notes": "Stage on ground first"}
        return self._session(agent="recommend_firmware_updates", query="firmware", context=response, response=response)

    def recommend_battery_replacements(self, *, soh: float = 1.0, cycles: int = 0) -> dict[str, Any]:
        replace = soh < 0.8 or cycles >= 200
        response = {"soh": soh, "cycles": cycles, "replace": replace, "advice": "Replace pack" if replace else "Continue use with monitoring"}
        return self._session(agent="recommend_battery_replacements", query="battery", context=response, response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        key = agent.lower().replace("-", "_")
        dispatch = {
            "monitor_all_aircraft": lambda: self.monitor_all_aircraft(aircraft=ctx.get("aircraft")),
            "predict_failures": lambda: self.predict_failures(telemetry=ctx.get("telemetry") or ctx),
            "predict_maintenance": lambda: self.predict_maintenance(flight_hours=float(ctx.get("flight_hours", 0)), cycles=int(ctx.get("cycles", 0))),
            "recommend_operators": lambda: self.recommend_operators(mission_type=query or ctx.get("mission_type", "survey"), candidates=ctx.get("candidates")),
            "optimize_missions_cloud": lambda: self.optimize_missions_cloud(missions=ctx.get("missions")),
            "optimize_fleet_usage": lambda: self.optimize_fleet_usage(fleets=ctx.get("fleets")),
            "detect_anomalies_cloud": lambda: self.detect_anomalies_cloud(samples=ctx.get("samples")),
            "generate_cloud_reports": lambda: self.generate_cloud_reports(period=query or ctx.get("period", "daily")),
            "recommend_firmware_updates": lambda: self.recommend_firmware_updates(current=ctx.get("current", ""), available=ctx.get("available", "")),
            "recommend_battery_replacements": lambda: self.recommend_battery_replacements(soh=float(ctx.get("soh", 1.0)), cycles=int(ctx.get("cycles", 0))),
        }
        if key in dispatch:
            return dispatch[key]()
        return super().assist(agent=agent, query=query, context=context)


from applications.drone_platform.shared.store import drone_store

cloud_ai = CloudAIAssistant(store=drone_store)
