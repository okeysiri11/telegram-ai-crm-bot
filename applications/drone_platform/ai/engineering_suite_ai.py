"""Engineering Suite AI — motors/props/batteries/frames recommendations (Sprint 11.5)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.vision_ai import VisionFlightAIAssistant


ENGINEERING_SUITE_AI_CAPABILITIES = (
    "recommend_motors",
    "recommend_propellers",
    "recommend_batteries",
    "recommend_escs",
    "recommend_frame",
    "detect_engineering_mistakes",
    "predict_failures",
    "estimate_endurance",
    "optimize_efficiency",
    "suggest_improvements",
    "explain_engineering_decisions",
)


class EngineeringSuiteAIAssistant(VisionFlightAIAssistant):
    def capabilities(self) -> list[str]:
        return list(dict.fromkeys([*super().capabilities(), *ENGINEERING_SUITE_AI_CAPABILITIES]))

    def recommend_motors(self, *, auw_kg: float, motors: int = 4, use_case: str = "multirotor") -> dict[str, Any]:
        thrust_each = (auw_kg * 2.0) / max(motors, 1)
        response = {
            "auw_kg": auw_kg,
            "motors": motors,
            "use_case": use_case,
            "target_thrust_per_motor_kgf": round(thrust_each, 3),
            "suggestions": ["MN4014-400" if auw_kg >= 2 else "2212-920", "Match KV to prop diameter and battery S-count"],
        }
        return self._session(agent="recommend_motors", query=use_case, context=response, response=response)

    def recommend_propellers(self, *, motor_kv: float, battery_s: int, airframe: str = "multirotor") -> dict[str, Any]:
        diameter = 15 if motor_kv < 500 else 10 if motor_kv < 1000 else 5
        response = {
            "motor_kv": motor_kv,
            "battery_s": battery_s,
            "airframe": airframe,
            "suggested_diameter_in": diameter,
            "notes": ["Validate tip speed < ~0.7 Mach", "Prefer matched pairs/sets"],
        }
        return self._session(agent="recommend_propellers", query=airframe, context=response, response=response)

    def recommend_batteries(self, *, voltage_needed: float, energy_wh: float, chemistry: str = "lipo") -> dict[str, Any]:
        series = max(1, round(voltage_needed / 3.7))
        response = {
            "chemistry": chemistry,
            "suggested_series": series,
            "energy_wh": energy_wh,
            "notes": ["Keep 20-25% reserve", "Size C-rating for peak current"],
        }
        return self._session(agent="recommend_batteries", query=chemistry, context=response, response=response)

    def recommend_escs(self, *, motor_max_amps: float, battery_s: int) -> dict[str, Any]:
        cont = motor_max_amps * 1.25
        response = {
            "motor_max_amps": motor_max_amps,
            "battery_s": battery_s,
            "suggested_cont_amps": round(cont, 1),
            "suggestions": ["FOC-60A" if cont > 40 else "BLHeli-30A"],
        }
        return self._session(agent="recommend_escs", query="esc", context=response, response=response)

    def recommend_frame(self, *, payload_kg: float, endurance_min: float, style: str = "multirotor") -> dict[str, Any]:
        response = {
            "style": style,
            "payload_kg": payload_kg,
            "endurance_min": endurance_min,
            "suggestion": "HEX-650" if payload_kg > 1.5 else "QR-X450" if style == "multirotor" else "FW-1.8M",
        }
        return self._session(agent="recommend_frame", query=style, context=response, response=response)

    def detect_engineering_mistakes(self, *, design: dict[str, Any]) -> dict[str, Any]:
        mistakes = []
        if float(design.get("twr", 2)) < 1.5:
            mistakes.append("Thrust-to-weight too low for safe hover margin")
        if design.get("cg_outside_limits"):
            mistakes.append("CG outside approved limits")
        if float(design.get("esc_amps", 100)) < float(design.get("motor_amps", 0)):
            mistakes.append("ESC continuous rating below motor current")
        response = {"mistakes": mistakes, "ok": not mistakes, "design": design}
        return self._session(agent="detect_engineering_mistakes", query="review", context=design, response=response)

    def predict_failures(self, *, stressors: list[str] | None = None) -> dict[str, Any]:
        stressors = list(stressors or [])
        predictions = []
        if "overcurrent" in stressors:
            predictions.append("ESC thermal shutdown / FET failure")
        if "vibration" in stressors:
            predictions.append("IMU clipping / EKF divergence")
        if "cold" in stressors:
            predictions.append("Battery voltage sag / reduced endurance")
        response = {"stressors": stressors, "predictions": predictions or ["No dominant failure mode identified"]}
        return self._session(agent="predict_failures", query="failures", context={"stressors": stressors}, response=response)

    def estimate_endurance(self, *, capacity_mah: float, average_current_a: float) -> dict[str, Any]:
        minutes = (capacity_mah / 1000.0) * 0.8 / max(average_current_a, 1e-9) * 60
        response = {"capacity_mah": capacity_mah, "average_current_a": average_current_a, "endurance_min": round(minutes, 2)}
        return self._session(agent="estimate_endurance", query="endurance", context=response, response=response)

    def optimize_efficiency(self, *, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        ranked = sorted(candidates, key=lambda c: float(c.get("efficiency_score", 0)), reverse=True)
        response = {"ranked": ranked, "best": ranked[0] if ranked else None}
        return self._session(agent="optimize_efficiency", query="efficiency", context={"count": len(candidates)}, response=response)

    def suggest_improvements(self, *, summary: dict[str, Any]) -> dict[str, Any]:
        response = {
            "summary": summary,
            "improvements": [
                "Increase thrust margin to >= 2:1 for multirotors",
                "Reduce harness resistance on high-current paths",
                "Document CG stations and re-check after payload changes",
            ],
        }
        return self._session(agent="suggest_improvements", query="improve", context=summary, response=response)

    def explain_engineering_decisions(self, *, decision: str, rationale: str = "") -> dict[str, Any]:
        response = {
            "decision": decision,
            "explanation": rationale or f"Decision '{decision}' should be justified by thrust, power, thermal, and CG constraints.",
            "checks": ["Safety margins", "Thermal path", "Manufacturability", "Maintainability"],
        }
        return self._session(agent="explain_engineering_decisions", query=decision, context={"rationale": rationale}, response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        key = agent.lower().replace("-", "_")
        dispatch = {
            "recommend_motors": lambda: self.recommend_motors(
                auw_kg=float(ctx.get("auw_kg", 1.5)), motors=int(ctx.get("motors", 4)), use_case=ctx.get("use_case", query or "multirotor")
            ),
            "recommend_propellers": lambda: self.recommend_propellers(
                motor_kv=float(ctx.get("motor_kv", 920)), battery_s=int(ctx.get("battery_s", 4)), airframe=ctx.get("airframe", "multirotor")
            ),
            "recommend_batteries": lambda: self.recommend_batteries(
                voltage_needed=float(ctx.get("voltage_needed", 14.8)),
                energy_wh=float(ctx.get("energy_wh", 100)),
                chemistry=ctx.get("chemistry", "lipo"),
            ),
            "recommend_escs": lambda: self.recommend_escs(
                motor_max_amps=float(ctx.get("motor_max_amps", 25)), battery_s=int(ctx.get("battery_s", 4))
            ),
            "recommend_frame": lambda: self.recommend_frame(
                payload_kg=float(ctx.get("payload_kg", 0.5)),
                endurance_min=float(ctx.get("endurance_min", 15)),
                style=ctx.get("style", query or "multirotor"),
            ),
            "detect_engineering_mistakes": lambda: self.detect_engineering_mistakes(design=ctx.get("design") or {"note": query}),
            "predict_failures": lambda: self.predict_failures(stressors=ctx.get("stressors") or [query]),
            "estimate_endurance": lambda: self.estimate_endurance(
                capacity_mah=float(ctx.get("capacity_mah", 5000)), average_current_a=float(ctx.get("average_current_a", 15))
            ),
            "optimize_efficiency": lambda: self.optimize_efficiency(candidates=ctx.get("candidates") or []),
            "suggest_improvements": lambda: self.suggest_improvements(summary=ctx.get("summary") or {"query": query}),
            "explain_engineering_decisions": lambda: self.explain_engineering_decisions(decision=query, rationale=ctx.get("rationale", "")),
        }
        if key in dispatch:
            return dispatch[key]()
        return super().assist(agent=agent, query=query, context=context)


from applications.drone_platform.shared.store import drone_store

engineering_suite_ai = EngineeringSuiteAIAssistant(store=drone_store)
