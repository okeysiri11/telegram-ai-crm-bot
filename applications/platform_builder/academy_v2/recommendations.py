"""Smart recommendations — Sprint 28.6."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.academy_v2.catalogs import RECOMMENDATION_TYPES
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


DEFAULT_RECS = {
    "ai_specialists": ["Medical AI", "Finance AI", "Legal AI"],
    "modules": ["CRM", "Knowledge Base", "Analytics", "Workflows"],
    "departments": ["Leadership", "Operations", "Support"],
    "dashboards": ["KPI Overview", "AI Team Status", "Organization Map"],
    "automations": ["Welcome sequence", "Renewal reminder"],
    "marketplace_apps": ["Booking widget", "Listing pack"],
    "knowledge_sources": ["SOPs", "Industry playbooks", "FAQ"],
}


class RecommendationEngine:
    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def recommend(self, *, builder_id: str = "vertical", industry: str | None = None) -> dict[str, Any]:
        items = []
        for kind in RECOMMENDATION_TYPES:
            kid = kind["id"]
            options = list(DEFAULT_RECS.get(kid, []))
            if industry == "medical" and kid == "ai_specialists":
                options = ["Medical AI", "Finance AI", "HR AI"]
            if industry == "legal" and kid == "ai_specialists":
                options = ["Legal AI", "Finance AI", "Analytics AI"]
            items.append(
                {
                    "type": kid,
                    "name": kind["name"],
                    "options": options,
                    "reason": f"Strong defaults for {builder_id}"
                    + (f" in {industry}" if industry else ""),
                }
            )
        record = {
            "recommendation_id": _id("arec"),
            "builder_id": builder_id,
            "industry": industry,
            "items": items,
            "created_at": _now(),
            "source": "academy_v2",
        }
        self.store.academy_recommendations.save(record["recommendation_id"], record)
        return record

    def list_all(self) -> dict[str, Any]:
        items = self.store.academy_recommendations.list_all()
        return {"count": len(items), "items": items}

    def status(self) -> dict[str, Any]:
        return {"ready": True, "operational": True, "types": list(RECOMMENDATION_TYPES), **self.list_all()}
