"""EMR integrations — Sprint 25.4."""

from __future__ import annotations

from typing import Any

from platform_migration.models import INTEGRATION_TARGETS, KPI_TARGETS


class MigrationIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "required_before_production": True,
        }
