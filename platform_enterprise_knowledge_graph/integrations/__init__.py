"""EKG integrations — Sprint 24.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_knowledge_graph.models import INTEGRATION_TARGETS, KPI_TARGETS


class KnowledgeGraphIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "central_context_source": True,
        }
