"""PIN integrations — Sprint 24.3."""

from __future__ import annotations

from typing import Any

from platform_predictive_intelligence.models import INTEGRATION_TARGETS, KPI_TARGETS


class PredictiveIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "shared_prediction_layer": True,
        }
