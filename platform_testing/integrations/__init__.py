"""ETI integrations — Sprint 25.1."""

from __future__ import annotations

from typing import Any

from platform_testing.models import INTEGRATION_TARGETS, KPI_TARGETS


class TestIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "duplicates_eqa_logic": False,
        }
