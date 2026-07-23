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




class QueryRouter:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def route(
        self,
        *,
        query: str,
        preferred_sources: list[str] | None = None,
        use_cache: bool = True,
        principal: str = "system",
    ) -> dict[str, Any]:
        if not query:
            raise ValidationError("query is required")
        preferred = list(preferred_sources or [])
        # pick optimal source by simple heuristic
        q = query.lower()
        if "vector" in q or "embed" in q:
            chosen = preferred[0] if preferred else "vector_db"
        elif "event" in q or "stream" in q:
            chosen = preferred[0] if preferred else "event_stream"
        elif preferred:
            chosen = preferred[0]
        else:
            chosen = "postgresql"
        rid = _id("edf_route")
        cached = False
        if use_cache:
            for c in self.store.edf_cache.list_all():
                if c.get("query") == query and c.get("source") == chosen:
                    cached = True
                    break
        return self.store.edf_routes.save(
            rid,
            {
                "route_id": rid,
                "query": query,
                "chosen_source": chosen,
                "preferred_sources": preferred,
                "use_cache": use_cache,
                "cache_hit": cached,
                "principal": principal,
                "policy_applied": True,
                "latency_ms": 2 if cached else 12,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        routes = self.store.edf_routes.list_all()
        return {
            "routes": len(routes),
            "cache_hits": sum(1 for r in routes if r.get("cache_hit")),
            "avg_latency_ms": (sum(r.get("latency_ms", 0) for r in routes) / len(routes)) if routes else 0,
        }
