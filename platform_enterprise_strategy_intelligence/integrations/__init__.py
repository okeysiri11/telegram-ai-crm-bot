"""EST integrations — Sprint 24.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_strategy_intelligence.models import INTEGRATION_TARGETS, KPI_TARGETS


class StrategyIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "pipeline": [
                "strategy_intelligence",
                "multi_agent_council",
                "owner_approval",
                "execution_workflow",
            ],
        }
