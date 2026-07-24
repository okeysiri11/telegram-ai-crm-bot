"""Visual Workflow Designer — Sprint 24.1."""

from __future__ import annotations

from typing import Any

from platform_workflow_intelligence.models import DESIGNER_NODES


class VisualWorkflowDesigner:
    def add_node(self, workflow: dict[str, Any], *, node_type: str, node_id: str = "", config: dict[str, Any] | None = None) -> dict[str, Any]:
        node_type = (node_type or "").lower()
        if node_type not in DESIGNER_NODES:
            raise ValueError(f"unsupported node: {node_type}")
        updated = dict(workflow)
        nodes = list(updated.get("nodes") or [])
        nid = node_id or f"{node_type}_{len(nodes)+1}"
        nodes.append({"node_id": nid, "type": node_type, "config": dict(config or {}), "drag_drop": True})
        updated["nodes"] = nodes
        return updated

    def palette(self) -> dict[str, Any]:
        return {"elements": list(DESIGNER_NODES), "drag_drop": True, "visual": True}
