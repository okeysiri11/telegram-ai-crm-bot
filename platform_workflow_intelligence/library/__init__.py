"""Workflow Library — Sprint 24.1."""

from __future__ import annotations

from typing import Any

from platform_workflow_intelligence.models import INDUSTRY_LIBRARY


class WorkflowLibrary:
    def catalog(self) -> dict[str, Any]:
        templates = []
        for industry in INDUSTRY_LIBRARY:
            templates.append(
                {
                    "industry": industry,
                    "template_id": f"tpl_{industry}_core",
                    "name": f"{industry.title()} Core Flow",
                    "nodes": ["start", "crm", "human_approval", "commerce", "notification", "end"],
                    "policy": "requires_owner",
                }
            )
        return {"industries": list(INDUSTRY_LIBRARY), "templates": templates, "count": len(templates)}

    def instantiate(self, *, industry: str, workflow_id: str, owner: str = "platform_owner") -> dict[str, Any]:
        industry = (industry or "").lower()
        if industry not in INDUSTRY_LIBRARY:
            raise ValueError(f"unsupported industry: {industry}")
        cat = self.catalog()
        tpl = next(t for t in cat["templates"] if t["industry"] == industry)
        return {
            "workflow_id": workflow_id,
            "name": tpl["name"],
            "description": f"Library template for {industry}",
            "industry": industry,
            "version": "1.0",
            "status": "draft",
            "owner": owner,
            "change_history": [{"version": "1.0", "event": "from_library"}],
            "nodes": [{"node_id": f"n{i}", "type": t, "config": {}, "drag_drop": True} for i, t in enumerate(tpl["nodes"])],
            "policy": tpl["policy"],
            "from_library": True,
        }
