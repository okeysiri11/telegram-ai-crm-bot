from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.digital_twin.relationship_manager import RelationshipManager


class VisualizationLayer:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.relationships = RelationshipManager(self.store)

    def render(self, *, view: str = "organization", root_id: str | None = None) -> dict[str, Any]:
        twins = self.store.edt_twins.list_all()
        graph = self.relationships.graph(root_id=root_id)
        by_type: dict[str, list] = {}
        for t in twins:
            by_type.setdefault(t.get("twin_type", "custom"), []).append(
                {"twin_id": t["twin_id"], "name": t.get("name"), "status": t.get("status")}
            )
        views = {
            "organization": by_type.get("organization", []) + by_type.get("department", []),
            "resources": by_type.get("warehouse", []) + by_type.get("equipment", []) + by_type.get("asset", []),
            "processes": by_type.get("project", []) + by_type.get("production", []),
            "equipment": by_type.get("equipment", []),
            "logistics": by_type.get("vehicle", []) + by_type.get("vessel", []),
            "ai_agents": by_type.get("ai_agent", []),
            "dependencies": graph,
        }
        payload = views.get(view, graph)
        vid = _id("edt_viz")
        return self.store.edt_visualizations.save(
            vid,
            {
                "visualization_id": vid,
                "view": view,
                "payload": payload,
                "available_views": list(views.keys()),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"visualizations": len(self.store.edt_visualizations.list_all())}
