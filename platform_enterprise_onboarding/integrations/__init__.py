"""Onboarding integrations — Sprint 22.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_onboarding.models import INTEGRATION_TARGETS, KPI_TARGETS


class OnboardingIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
        }
