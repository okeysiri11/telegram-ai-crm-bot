"""EPL integrations — Sprint 25.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_performance_testing.models import INTEGRATION_TARGETS, KPI_TARGETS


class PerformanceTestingIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "duplicates_epf_logic": False,
            "required_before_production": True,
        }
