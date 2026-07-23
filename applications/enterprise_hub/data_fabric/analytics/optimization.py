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



class OptimizationAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        routes = self.store.edf_routes.list_all()
        avg = (sum(r.get("latency_ms", 0) for r in routes) / len(routes)) if routes else 0
        suggestions = []
        if avg > 10:
            suggestions.append("increase smart cache TTL for hot queries")
        if sum(1 for r in routes if r.get("cache_hit")) < max(1, len(routes) // 3):
            suggestions.append("pre-warm federation result cache")
        rid = _id("edf_opt")
        return self.store.edf_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "optimization",
                "avg_latency_ms": avg,
                "suggestions": suggestions or ["system healthy"],
                "at": _now(),
            },
        )
