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



class QualityAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        items = self.store.edf_quality.list_all()
        rid = _id("edf_qan")
        return self.store.edf_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "quality",
                "assessments": len(items),
                "avg_score": (sum(i.get("score", 0) for i in items) / len(items)) if items else 0,
                "failed": sum(1 for i in items if not i.get("passed")),
                "at": _now(),
            },
        )
