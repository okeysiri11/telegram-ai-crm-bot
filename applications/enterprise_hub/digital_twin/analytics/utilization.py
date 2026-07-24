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



class UtilizationAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        resources = [
            t for t in self.store.edt_twins.list_all()
            if t.get("twin_type") in ("equipment", "warehouse", "vehicle", "vessel", "production", "asset")
        ]
        utilized = sum(1 for t in resources if (t.get("state") or {}).get("utilization", 0) >= 0.5)
        rid = _id("edt_util")
        return self.store.edt_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "utilization",
                "resources": len(resources),
                "utilized": utilized,
                "utilization_rate": (utilized / len(resources)) if resources else 0,
                "at": _now(),
            },
        )
