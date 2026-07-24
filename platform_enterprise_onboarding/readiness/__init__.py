"""Readiness Analyzer — Sprint 22.9."""

from __future__ import annotations

from typing import Any


class ReadinessAnalyzer:
    def analyze(
        self,
        *,
        wizard: dict[str, Any] | None = None,
        imports: list[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
        security_ok: bool = True,
        integrations_ok: bool = True,
    ) -> dict[str, Any]:
        wizard = wizard or {}
        imports = list(imports or [])
        config = config or {}
        checks = {
            "data_completeness": bool(wizard.get("company_name")) and bool(imports),
            "settings_correct": bool(wizard.get("currency")) and bool(wizard.get("working_hours")),
            "access_rights": bool(wizard.get("roles")),
            "security": security_ok,
            "integrations": integrations_ok,
            "ai_modules_ready": bool(
                config.get("ai_business_advisor_activated")
                and config.get("ai_marketing_os_activated")
                and config.get("product_intelligence_activated")
            ),
        }
        score = sum(1 for v in checks.values() if v) / len(checks)
        return {
            "checks": checks,
            "score": round(score, 3),
            "ready": score >= 1.0,
            "report": "ready_for_go_live" if score >= 1.0 else "gaps_remain",
        }
