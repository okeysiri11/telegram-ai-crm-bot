"""Telemetry / Flight Log / Diagnostics AI Assistant (Sprint 11.3)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.firmware_ai import FirmwareAIAssistant


TELEMETRY_AI_CAPABILITIES = (
    "explain_mavlink_message",
    "interpret_telemetry",
    "analyze_flight_log",
    "diagnose_flight",
    "summarize_mission_risk",
    "suggest_emergency_landing",
    "explain_failsafe_event",
)


class TelemetryFlightAIAssistant(FirmwareAIAssistant):
    """Extends firmware AI with MAVLink, telemetry, and flight diagnostics assistance."""

    def capabilities(self) -> list[str]:
        return list(dict.fromkeys([*super().capabilities(), *TELEMETRY_AI_CAPABILITIES]))

    def explain_mavlink_message(self, *, msg_name: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {
            "msg_name": msg_name.upper(),
            "explanation": f"{msg_name.upper()} carries vehicle/state fields used by GCS and autopilot links.",
            "fields": dict(fields or {}),
            "tips": ["Validate units", "Cross-check with HEARTBEAT system status", "Log anomalies for post-flight review"],
        }
        return self._session(agent="explain_mavlink_message", query=msg_name, context={"fields": fields}, response=response)

    def interpret_telemetry(self, *, summary: dict[str, Any]) -> dict[str, Any]:
        response = {
            "summary": summary,
            "interpretation": "Review GPS, battery, link quality, and failsafe analyzers together before concluding root cause.",
            "priority_checks": ["gps_quality", "battery", "radio_link", "failsafe"],
        }
        return self._session(agent="interpret_telemetry", query="telemetry", context=summary, response=response)

    def analyze_flight_log(self, *, findings: list[str] | None = None, log_type: str = "") -> dict[str, Any]:
        response = {
            "log_type": log_type,
            "findings": list(findings or []),
            "method": ["Parse messages", "Correlate STATUSTEXT", "Align with mission timeline", "Flag crash/power indicators"],
        }
        return self._session(agent="analyze_flight_log", query=log_type or "log", context={"findings": findings}, response=response)

    def diagnose_flight(self, *, detections: list[str] | None = None) -> dict[str, Any]:
        dets = list(detections or [])
        response = {
            "detections": dets,
            "guidance": [
                "Reproduce with bench logs if possible",
                "Compare against last healthy flight",
                "Inspect sensor calibration and power path",
            ],
            "severity": "critical" if "crash_indicator" in dets or "power_failure" in dets else "warning" if dets else "ok",
        }
        return self._session(agent="diagnose_flight", query="diagnostics", context={"detections": dets}, response=response)

    def summarize_mission_risk(self, *, risk: dict[str, Any]) -> dict[str, Any]:
        response = {
            "risk": risk,
            "summary": f"Mission risk level is {risk.get('risk_level', 'unknown')} (score {risk.get('risk_score')}).",
            "actions": ["Confirm battery reserve", "Review geofence", "Validate RTH path"],
        }
        return self._session(agent="summarize_mission_risk", query="risk", context=risk, response=response)

    def suggest_emergency_landing(self, *, suggestions: dict[str, Any]) -> dict[str, Any]:
        response = {
            "suggestions": suggestions,
            "policy": "engineering_assistance_only",
            "note": "Prefer predefined rally points and clear terrain when available.",
        }
        return self._session(agent="suggest_emergency_landing", query="emergency", context=suggestions, response=response)

    def explain_failsafe_event(self, *, event_type: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {
            "event_type": event_type,
            "explanation": f"Failsafe event '{event_type}' indicates the autopilot entered a protective mode.",
            "details": dict(details or {}),
            "checks": ["RC/telemetry link", "Battery failsafe thresholds", "GCS heartbeat"],
        }
        return self._session(agent="explain_failsafe_event", query=event_type, context=dict(details or {}), response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        agent_key = agent.lower().replace("-", "_")
        dispatch = {
            "explain_mavlink_message": lambda: self.explain_mavlink_message(
                msg_name=query, fields=ctx.get("fields")
            ),
            "interpret_telemetry": lambda: self.interpret_telemetry(summary=ctx.get("summary") or {"query": query}),
            "analyze_flight_log": lambda: self.analyze_flight_log(
                findings=ctx.get("findings"), log_type=ctx.get("log_type", query)
            ),
            "diagnose_flight": lambda: self.diagnose_flight(detections=ctx.get("detections") or [query]),
            "summarize_mission_risk": lambda: self.summarize_mission_risk(risk=ctx.get("risk") or {"note": query}),
            "suggest_emergency_landing": lambda: self.suggest_emergency_landing(
                suggestions=ctx.get("suggestions") or {"query": query}
            ),
            "explain_failsafe_event": lambda: self.explain_failsafe_event(
                event_type=query, details=ctx.get("details")
            ),
        }
        if agent_key in dispatch:
            return dispatch[agent_key]()
        return super().assist(agent=agent, query=query, context=context)


from applications.drone_platform.shared.store import drone_store

telemetry_flight_ai = TelemetryFlightAIAssistant(store=drone_store)
