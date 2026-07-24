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



class RecommendationAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self, *, process_id: str) -> dict[str, Any]:
        opts = [o for o in self.store.epm_optimizations.list_all() if o.get("process_id") == process_id]
        recs = []
        for o in opts:
            for s in o.get("suggestions") or []:
                recs.append(s)
        rid = _id("epm_rec")
        return self.store.epm_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "recommendations",
                "process_id": process_id,
                "recommendations": recs[:20],
                "count": len(recs),
                "at": _now(),
            },
        )
