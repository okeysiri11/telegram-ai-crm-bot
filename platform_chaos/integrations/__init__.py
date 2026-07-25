"""ECE integrations — Sprint 25.3."""

from __future__ import annotations

from typing import Any

from platform_chaos.models import INTEGRATION_TARGETS, KPI_TARGETS


class ChaosIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "required_before_production": True,
        }
