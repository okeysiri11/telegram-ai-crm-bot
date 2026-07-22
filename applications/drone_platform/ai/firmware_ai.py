"""Firmware AI Assistant extensions — engineering-only firmware intelligence."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.assistant import EngineeringAIAssistant


FIRMWARE_AI_CAPABILITIES = (
    "explain_firmware",
    "find_bugs",
    "suggest_optimizations",
    "generate_patches",
    "suggest_parameter_tuning",
    "generate_configuration_presets",
    "compare_firmware_versions",
    "summarize_release_changes",
)


class FirmwareAIAssistant(EngineeringAIAssistant):
    """Extends engineering AI with firmware-specific assistive capabilities."""

    def capabilities(self) -> list[str]:
        return list(dict.fromkeys([*super().capabilities(), *FIRMWARE_AI_CAPABILITIES]))

    def explain_firmware(self, *, stack: str, version: str = "", summary: str = "") -> dict[str, Any]:
        response = {
            "stack": stack,
            "version": version,
            "explanation": (
                f"{stack} firmware {version or ''}".strip()
                + " should be understood via official docs, release notes, and parameter defaults."
            ),
            "engineering_focus": [
                "Identify airframe target and sensor set",
                "Review failsafe and fence defaults before flight tests",
                "Keep a parameter backup before upgrades",
            ],
            "notes": summary,
        }
        return self._session(
            agent="explain_firmware",
            query=f"{stack}:{version}",
            context={"stack": stack, "version": version},
            response=response,
        )

    def find_bugs(self, *, symptoms: list[str] | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {
            "likely_areas": ["parameter mismatch", "sensor orientation", "build flag inconsistency"],
            "symptoms": list(symptoms or []),
            "method": [
                "Reproduce on bench",
                "Diff parameters against last known-good",
                "Inspect recent patches/builds",
            ],
            "context": dict(context or {}),
        }
        return self._session(agent="find_bugs", query="bugs", context=dict(context or {}), response=response)

    def suggest_optimizations(self, *, stack: str, goals: list[str] | None = None) -> dict[str, Any]:
        response = {
            "stack": stack,
            "goals": list(goals or ["stability", "logging"]),
            "suggestions": [
                "Enable structured logging for tuning sessions",
                "Reduce simultaneous experimental parameter changes",
                "Prefer release builds for field validation after debug cycles",
            ],
        }
        return self._session(agent="suggest_optimizations", query=stack, context={"goals": goals}, response=response)

    def generate_patches(self, *, title: str, intent: str, base_version: str = "") -> dict[str, Any]:
        response = {
            "title": title,
            "base_version": base_version,
            "proposed_diff": f"# engineering patch proposal: {title}\n# intent: {intent}\n# review before apply\n",
            "policy": "Assistive patch draft only — human review required",
        }
        return self._session(
            agent="generate_patches",
            query=title,
            context={"intent": intent, "base_version": base_version},
            response=response,
        )

    def suggest_parameter_tuning(self, *, vehicle: str, issue: str) -> dict[str, Any]:
        response = {
            "vehicle": vehicle,
            "issue": issue,
            "tuning_steps": [
                "Change one related parameter group at a time",
                "Validate on the ground / short hops as appropriate and legal",
                "Record before/after parameter sets",
            ],
        }
        return self._session(agent="suggest_parameter_tuning", query=issue, context={"vehicle": vehicle}, response=response)

    def generate_configuration_presets(self, *, vehicle: str, use_case: str = "default") -> dict[str, Any]:
        from applications.drone_platform.firmware.configuration import firmware_configuration_manager

        preset = firmware_configuration_manager.preset(vehicle=vehicle, use_case=use_case)
        return self._session(
            agent="generate_configuration_presets",
            query=f"{vehicle}:{use_case}",
            context={"vehicle": vehicle, "use_case": use_case},
            response={"preset": preset},
        )

    def compare_firmware_versions(self, *, left: str, right: str, notes: str = "") -> dict[str, Any]:
        response = {
            "left": left,
            "right": right,
            "comparison": [
                "Review official release notes between versions",
                "Diff parameter defaults and deprecated keys",
                "Re-validate sensors and failsafes after upgrade",
            ],
            "notes": notes,
        }
        return self._session(
            agent="compare_firmware_versions",
            query=f"{left}->{right}",
            context={"left": left, "right": right},
            response=response,
        )

    def summarize_release_changes(self, *, version: str, notes: str = "") -> dict[str, Any]:
        response = {
            "version": version,
            "summary": notes or f"Engineering summary for firmware release {version}",
            "checklist": ["Read release notes", "Backup params", "Bench flash", "Validate sensors"],
        }
        return self._session(agent="summarize_release_changes", query=version, context={"notes": notes}, response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        agent_key = agent.lower().replace("-", "_")
        firmware_dispatch = {
            "explain_firmware": lambda: self.explain_firmware(
                stack=ctx.get("stack", query), version=ctx.get("version", ""), summary=ctx.get("summary", "")
            ),
            "find_bugs": lambda: self.find_bugs(symptoms=ctx.get("symptoms") or [query], context=ctx),
            "suggest_optimizations": lambda: self.suggest_optimizations(
                stack=ctx.get("stack", "ardupilot"), goals=ctx.get("goals")
            ),
            "generate_patches": lambda: self.generate_patches(
                title=query, intent=ctx.get("intent", query), base_version=ctx.get("base_version", "")
            ),
            "suggest_parameter_tuning": lambda: self.suggest_parameter_tuning(
                vehicle=ctx.get("vehicle", "copter"), issue=query
            ),
            "generate_configuration_presets": lambda: self.generate_configuration_presets(
                vehicle=ctx.get("vehicle", query), use_case=ctx.get("use_case", "default")
            ),
            "compare_firmware_versions": lambda: self.compare_firmware_versions(
                left=ctx.get("left", ""), right=ctx.get("right", query), notes=ctx.get("notes", "")
            ),
            "summarize_release_changes": lambda: self.summarize_release_changes(
                version=query, notes=ctx.get("notes", "")
            ),
        }
        if agent_key in firmware_dispatch:
            return firmware_dispatch[agent_key]()
        return super().assist(agent=agent, query=query, context=context)


from applications.drone_platform.shared.store import drone_store

firmware_ai = FirmwareAIAssistant(store=drone_store)
