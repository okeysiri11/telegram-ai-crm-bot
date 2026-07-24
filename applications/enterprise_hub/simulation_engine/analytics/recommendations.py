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

    def report(self) -> dict[str, Any]:
        opts = self.store.esi_optimizations.list_all()
        decisions = self.store.esi_decisions.list_all()
        recs = [o.get("recommendation") for o in opts if o.get("recommendation")]
        for d in decisions:
            best = d.get("best_option")
            if best:
                recs.append(f"prefer decision option {best}")
        rid = _id("esi_rec")
        return self.store.esi_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "recommendations",
                "recommendations": recs[:20],
                "count": len(recs),
                "at": _now(),
            },
        )
