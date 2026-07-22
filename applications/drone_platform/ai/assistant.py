"""AI Engineering Assistant — helps engineers understand and improve UAV systems.

Scope is limited to legitimate engineering assistance:
firmware analysis, configuration review, parameter explanation, log interpretation,
hardware compatibility, troubleshooting, documentation, build recommendations, and diagnostics.

This assistant must not generate functionality intended for misuse.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


AGENT_CAPABILITIES = (
    "firmware_analysis",
    "configuration_review",
    "parameter_explanation",
    "log_interpretation",
    "hardware_compatibility",
    "troubleshooting",
    "engineering_documentation",
    "build_recommendations",
    "diagnostics",
)


class EngineeringAIAssistant:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def capabilities(self) -> list[str]:
        return list(AGENT_CAPABILITIES)

    def _session(
        self,
        *,
        agent: str,
        query: str,
        context: dict[str, Any],
        response: dict[str, Any],
    ) -> dict[str, Any]:
        sid = f"ai_{uuid.uuid4().hex[:12]}"
        record = {
            "session_id": sid,
            "agent": agent,
            "query": query,
            "context": dict(context),
            "response": dict(response),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "policy": "engineering_assistance_only",
        }
        self.store.ai_sessions.save(sid, record)
        return record

    def analyze_firmware(self, *, stack: str, version: str = "", notes: str = "") -> dict[str, Any]:
        response = {
            "summary": f"Firmware analysis for {stack} {version}".strip(),
            "recommendations": [
                "Verify parameter set against airframe defaults",
                "Confirm sensor calibration status before flight tests",
                "Archive current configuration before upgrades",
            ],
            "notes": notes or "Review release notes and known issues for this stack version.",
        }
        return self._session(agent="firmware_analysis", query=f"{stack}:{version}", context={"stack": stack, "version": version}, response=response)

    def review_configuration(self, *, parameters: dict[str, Any], stack: str = "") -> dict[str, Any]:
        flagged = [k for k, v in parameters.items() if isinstance(v, (int, float)) and abs(float(v)) > 1e6]
        response = {
            "parameter_count": len(parameters),
            "flagged_parameters": flagged,
            "findings": [
                "Configuration structure looks parseable",
                "Compare against a known-good template for this airframe",
            ],
            "stack": stack,
        }
        return self._session(agent="configuration_review", query="review", context={"parameters": parameters, "stack": stack}, response=response)

    def explain_parameter(self, *, name: str, value: Any = None, stack: str = "") -> dict[str, Any]:
        response = {
            "parameter": name,
            "value": value,
            "stack": stack,
            "explanation": (
                f"Parameter '{name}' controls an engineering configuration value. "
                "Confirm units and limits in the official firmware documentation before changing it."
            ),
            "guidance": "Change one parameter at a time and validate on the bench when possible.",
        }
        return self._session(agent="parameter_explanation", query=name, context={"name": name, "value": value, "stack": stack}, response=response)

    def interpret_log(self, *, log_summary: str, events: list[str] | None = None) -> dict[str, Any]:
        response = {
            "interpretation": "Log summary reviewed for engineering diagnostics.",
            "events": list(events or []),
            "next_steps": [
                "Correlate timestamps with configuration changes",
                "Check sensor health messages around anomalies",
                "Reproduce on a safe bench setup when practical",
            ],
            "input_preview": log_summary[:500],
        }
        return self._session(agent="log_interpretation", query="log", context={"log_summary": log_summary}, response=response)

    def check_hardware_compatibility(self, *, components: list[dict[str, Any]]) -> dict[str, Any]:
        response = {
            "component_count": len(components),
            "status": "review_required",
            "notes": [
                "Validate voltage domains across power module, ESC, and FC",
                "Confirm protocol compatibility for GPS, radio, and companion computer links",
                "Check physical mounting and CG impact for payloads",
            ],
            "components": components,
        }
        return self._session(agent="hardware_compatibility", query="compat", context={"components": components}, response=response)

    def troubleshoot(self, *, symptom: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {
            "symptom": symptom,
            "checklist": [
                "Confirm power and wiring integrity",
                "Review recent firmware/parameter changes",
                "Inspect sensor calibration and orientation",
                "Validate radio link and failsafe settings in a safe environment",
            ],
            "context": dict(context or {}),
        }
        return self._session(agent="troubleshooting", query=symptom, context=dict(context or {}), response=response)

    def draft_documentation(self, *, topic: str, details: str = "") -> dict[str, Any]:
        response = {
            "title": f"Engineering note: {topic}",
            "outline": [
                "Purpose and scope",
                "Hardware/firmware context",
                "Procedure or configuration steps",
                "Verification and acceptance criteria",
                "Revision history",
            ],
            "draft": details or f"Document engineering guidance for: {topic}",
        }
        return self._session(agent="engineering_documentation", query=topic, context={"topic": topic}, response=response)

    def recommend_build(self, *, airframe: str, use_case: str = "engineering_test") -> dict[str, Any]:
        response = {
            "airframe": airframe,
            "use_case": use_case,
            "recommendations": [
                "Select FC and ESC stack matched to motor current draw",
                "Size battery for required endurance with margin",
                "Include telemetry and logging for development flights",
                "Document BOM and wiring before first assembly",
            ],
        }
        return self._session(agent="build_recommendations", query=airframe, context={"airframe": airframe, "use_case": use_case}, response=response)

    def diagnose(self, *, system: str, observations: list[str] | None = None) -> dict[str, Any]:
        response = {
            "system": system,
            "observations": list(observations or []),
            "diagnostic_plan": [
                "Isolate subsystem (power, sensors, propulsion, links)",
                "Capture logs and parameter snapshot",
                "Compare against last known-good configuration",
                "Apply minimal corrective change and retest",
            ],
        }
        return self._session(agent="diagnostics", query=system, context={"system": system}, response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        agent_key = agent.lower().replace("-", "_")
        if agent_key not in AGENT_CAPABILITIES:
            return self._session(
                agent="unsupported",
                query=query,
                context=ctx,
                response={
                    "error": "unsupported_agent",
                    "supported": list(AGENT_CAPABILITIES),
                    "policy": "engineering_assistance_only",
                },
            )
        dispatch = {
            "firmware_analysis": lambda: self.analyze_firmware(stack=ctx.get("stack", "ardupilot"), version=ctx.get("version", ""), notes=query),
            "configuration_review": lambda: self.review_configuration(parameters=ctx.get("parameters", {}), stack=ctx.get("stack", "")),
            "parameter_explanation": lambda: self.explain_parameter(name=query, value=ctx.get("value"), stack=ctx.get("stack", "")),
            "log_interpretation": lambda: self.interpret_log(log_summary=query, events=ctx.get("events")),
            "hardware_compatibility": lambda: self.check_hardware_compatibility(components=ctx.get("components", [])),
            "troubleshooting": lambda: self.troubleshoot(symptom=query, context=ctx),
            "engineering_documentation": lambda: self.draft_documentation(topic=query, details=ctx.get("details", "")),
            "build_recommendations": lambda: self.recommend_build(airframe=query, use_case=ctx.get("use_case", "engineering_test")),
            "diagnostics": lambda: self.diagnose(system=query, observations=ctx.get("observations")),
        }
        return dispatch[agent_key]()

    def list_sessions(self) -> list[dict[str, Any]]:
        return self.store.ai_sessions.list_all()


engineering_ai = EngineeringAIAssistant()
