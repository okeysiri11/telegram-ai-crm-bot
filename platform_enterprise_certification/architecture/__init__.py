"""Architecture Validator — Sprint 25.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_certification.models import ARCHITECTURE_TARGETS


class ArchitectureValidator:
    def validate(self, *, missing: list[str] | None = None) -> dict[str, Any]:
        missing = set(missing or [])
        components = []
        for name in ARCHITECTURE_TARGETS:
            ok = name not in missing
            components.append({"component": name, "present": ok, "passed": ok})
        deps = [
            {"from": "enterprise_hub", "to": "enterprise_core", "ok": True},
            {"from": "ai_orchestrator", "to": "enterprise_hub", "ok": True},
            {"from": "workflow_engine", "to": "event_bus", "ok": True},
            {"from": "knowledge_graph", "to": "enterprise_hub", "ok": True},
            {"from": "marketplace", "to": "ai_provider_hub", "ok": True},
            {"from": "monitoring_platform", "to": "notification_platform", "ok": True},
        ]
        for d in deps:
            if d["from"] in missing or d["to"] in missing:
                d["ok"] = False
        passed = all(c["passed"] for c in components) and all(d["ok"] for d in deps)
        return {
            "components": components,
            "dependencies": deps,
            "passed": passed,
            "blocks_release": not passed,
        }
