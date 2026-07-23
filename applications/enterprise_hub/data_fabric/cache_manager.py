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




class CacheManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def put(
        self,
        *,
        query: str,
        source: str,
        result: dict[str, Any] | None = None,
        kind: str = "query",
        ttl_sec: int = 300,
    ) -> dict[str, Any]:
        if not query:
            raise ValidationError("query is required")
        cid = _id("edf_cache")
        return self.store.edf_cache.save(
            cid,
            {
                "cache_id": cid,
                "query": query,
                "source": source,
                "kind": kind,
                "result": result or {},
                "ttl_sec": ttl_sec,
                "hits": 0,
                "cached_at": _now(),
            },
        )

    def get(self, *, query: str, source: str) -> dict[str, Any] | None:
        for c in self.store.edf_cache.list_all():
            if c.get("query") == query and c.get("source") == source:
                c["hits"] = int(c.get("hits", 0)) + 1
                self.store.edf_cache.save(c["cache_id"], c)
                return c
        return None

    def status(self) -> dict[str, Any]:
        items = self.store.edf_cache.list_all()
        return {"entries": len(items), "total_hits": sum(int(i.get("hits", 0)) for i in items)}
