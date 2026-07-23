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



class UsageAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        routes = self.store.edf_routes.list_all()
        feds = self.store.edf_federations.list_all()
        cache = self.store.edf_cache.list_all()
        rid = _id("edf_usage")
        return self.store.edf_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "usage",
                "query_count": len(routes),
                "federation_count": len(feds),
                "cache_entries": len(cache),
                "cache_hits": sum(int(c.get("hits", 0)) for c in cache),
                "at": _now(),
            },
        )
