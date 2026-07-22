"""AI Safety Assistant — failures, nav confidence, safe actions, risk, reports (Sprint 11.9)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.cloud_ai import CloudAIAssistant


SAFETY_AI_CAPABILITIES = (
    "predict_failures_safety",
    "estimate_navigation_confidence",
    "recommend_safe_actions",
    "detect_abnormal_behavior",
    "estimate_mission_risk",
    "generate_safety_reports",
    "explain_recommendations",
)


class SafetyAIAssistant(CloudAIAssistant):
    def capabilities(self) -> list[str]:
        return list(dict.fromkeys([*super().capabilities(), *SAFETY_AI_CAPABILITIES]))

    def predict_failures_safety(self, *, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        s = dict(signals or {})
        vib = float(s.get("vibration", 0.2))
        link_q = float(s.get("link_quality", 0.9))
        conf = float(s.get("nav_confidence", 0.8))
        risk = "high" if vib > 0.8 or link_q < 0.3 or conf < 0.3 else "medium" if vib > 0.5 or link_q < 0.5 else "low"
        response = {"failure_risk": risk, "signals": s, "advice": "Prepare RTL" if risk != "low" else "Continue with monitoring"}
        return self._session(agent="predict_failures_safety", query="failures", context=s, response=response)

    def estimate_navigation_confidence(self, *, sources: list[str] | None = None, gps_ok: bool = True, drift_m: float = 0) -> dict[str, Any]:
        sources = list(sources or [])
        score = 0.2 * len(sources) + (0.4 if gps_ok else 0) - min(0.4, drift_m / 50)
        score = max(0.0, min(1.0, score))
        level = "high" if score >= 0.75 else "medium" if score >= 0.45 else "low"
        response = {"confidence": round(score, 3), "level": level, "sources": sources, "gps_ok": gps_ok, "drift_m": drift_m}
        return self._session(agent="estimate_navigation_confidence", query="confidence", context=response, response=response)

    def recommend_safe_actions(self, *, situation: str = "", violations: list[str] | None = None) -> dict[str, Any]:
        violations = list(violations or [])
        actions = []
        if "battery_critical" in violations or "battery" in situation.lower():
            actions.append("rtl_or_land_nearest")
        if "geofence_breach" in violations or any(v.startswith("nofly") for v in violations):
            actions.append("hold_and_exit_zone")
        if "link" in situation.lower() or not actions:
            actions.append("switch_link_and_assess")
        if not actions:
            actions.append("continue_with_heightened_monitoring")
        response = {"situation": situation, "violations": violations, "actions": actions, "policy": "engineering_assistance_only"}
        return self._session(agent="recommend_safe_actions", query=situation or "safe", context=response, response=response)

    def detect_abnormal_behavior(self, *, samples: list[float] | None = None) -> dict[str, Any]:
        samples = list(samples or [])
        mean = sum(samples) / len(samples) if samples else 0.0
        outliers = [x for x in samples if abs(x - mean) > max(1.0, abs(mean) * 0.4)]
        response = {"abnormal": bool(outliers), "outlier_count": len(outliers), "outliers": outliers[:10]}
        return self._session(agent="detect_abnormal_behavior", query="behavior", context=response, response=response)

    def estimate_mission_risk(self, *, nav_confidence: float = 0.8, link_quality: float = 0.9, battery_pct: float = 80, weather_ok: bool = True) -> dict[str, Any]:
        score = 100
        score -= int((1 - nav_confidence) * 40)
        score -= int((1 - link_quality) * 25)
        score -= 20 if battery_pct < 30 else 10 if battery_pct < 40 else 0
        score -= 15 if not weather_ok else 0
        level = "low" if score >= 75 else "medium" if score >= 50 else "high"
        response = {"risk_score": max(0, score), "risk_level": level, "nav_confidence": nav_confidence, "link_quality": link_quality, "battery_pct": battery_pct, "weather_ok": weather_ok}
        return self._session(agent="estimate_mission_risk", query="risk", context=response, response=response)

    def generate_safety_reports(self, *, period: str = "flight") -> dict[str, Any]:
        response = {
            "period": period,
            "sections": ["navigation_health", "link_quality", "geofence", "protections", "recoveries", "recommendations"],
            "status": "generated",
        }
        return self._session(agent="generate_safety_reports", query=period, context=response, response=response)

    def explain_recommendations(self, *, recommendation: str = "", context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        response = {
            "recommendation": recommendation,
            "explanation": f"Recommended '{recommendation}' based on current resilience signals to preserve aircraft and mission safety.",
            "context": ctx,
            "policy": "engineering_assistance_only",
        }
        return self._session(agent="explain_recommendations", query=recommendation or "explain", context=ctx, response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        key = agent.lower().replace("-", "_")
        dispatch = {
            "predict_failures_safety": lambda: self.predict_failures_safety(signals=ctx.get("signals") or ctx),
            "estimate_navigation_confidence": lambda: self.estimate_navigation_confidence(
                sources=ctx.get("sources"),
                gps_ok=bool(ctx.get("gps_ok", True)),
                drift_m=float(ctx.get("drift_m", 0)),
            ),
            "recommend_safe_actions": lambda: self.recommend_safe_actions(situation=query or ctx.get("situation", ""), violations=ctx.get("violations")),
            "detect_abnormal_behavior": lambda: self.detect_abnormal_behavior(samples=ctx.get("samples")),
            "estimate_mission_risk": lambda: self.estimate_mission_risk(
                nav_confidence=float(ctx.get("nav_confidence", 0.8)),
                link_quality=float(ctx.get("link_quality", 0.9)),
                battery_pct=float(ctx.get("battery_pct", 80)),
                weather_ok=bool(ctx.get("weather_ok", True)),
            ),
            "generate_safety_reports": lambda: self.generate_safety_reports(period=query or ctx.get("period", "flight")),
            "explain_recommendations": lambda: self.explain_recommendations(recommendation=query or ctx.get("recommendation", ""), context=ctx),
        }
        if key in dispatch:
            return dispatch[key]()
        return super().assist(agent=agent, query=query, context=context)


from applications.drone_platform.shared.store import drone_store

safety_ai = SafetyAIAssistant(store=drone_store)
