"""Client Journey integrations — Sprint 22.4."""

from __future__ import annotations

from typing import Any

from platform_beauty_client_journey.models import INTEGRATION_TARGETS, KPI_TARGETS


class JourneyIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "kpi_targets": dict(KPI_TARGETS),
        }
