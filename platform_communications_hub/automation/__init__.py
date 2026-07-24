"""Automation Engine — Sprint 22.6."""

from __future__ import annotations

from typing import Any

from platform_communications_hub.models import AUTOMATION_SCENARIOS


class AutomationEngine:
    def create(
        self,
        *,
        scenario: str,
        channel: str = "sms",
        template_name: str = "",
        pre_approved: bool = True,
        industry: str = "beauty",
    ) -> dict[str, Any]:
        if scenario not in AUTOMATION_SCENARIOS:
            raise ValueError(f"unknown automation scenario: {scenario}")
        return {
            "scenario": scenario,
            "channel": channel,
            "template_name": template_name or scenario,
            "pre_approved": pre_approved,
            "industry": industry,
            "enabled": True,
            "status": "active" if pre_approved else "pending_owner",
        }

    def scenarios(self) -> list[str]:
        return list(AUTOMATION_SCENARIOS)
