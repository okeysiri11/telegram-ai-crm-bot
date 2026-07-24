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



class EfficiencyAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self, *, process_id: str) -> dict[str, Any]:
        perfs = [p for p in self.store.epm_performance.list_all() if p.get("process_id") == process_id]
        eff = perfs[-1].get("efficiency", 0.7) if perfs else 0.7
        eid = _id("epm_eff")
        return self.store.epm_analytics.save(
            eid,
            {
                "analytics_id": eid,
                "kind": "efficiency",
                "process_id": process_id,
                "efficiency": eff,
                "waste_pct": round((1 - float(eff)) * 100, 2),
                "at": _now(),
            },
        )
