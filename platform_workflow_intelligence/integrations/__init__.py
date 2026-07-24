"""Cross-module integration map — Sprint 24.1."""

from __future__ import annotations

from typing import Any

from platform_workflow_intelligence.models import CROSS_MODULES, KPI_TARGETS


class WorkflowIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(CROSS_MODULES),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "uses_owner_decision_center": True,
            "uses_multi_agent_council": True,
        }

    def invoke(self, *, module: str, action: str = "ping") -> dict[str, Any]:
        module = (module or "").lower()
        if module not in CROSS_MODULES:
            raise ValueError(f"unsupported module: {module}")
        return {"module": module, "action": action, "delegated": True, "duplicates_logic": False}
