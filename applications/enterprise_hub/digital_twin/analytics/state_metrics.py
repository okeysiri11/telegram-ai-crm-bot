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



class StateMetrics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        twins = self.store.edt_twins.list_all()
        active = sum(1 for t in twins if t.get("status") == "active")
        rid = _id("edt_sm")
        return self.store.edt_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "state_metrics",
                "total_twins": len(twins),
                "active_twins": active,
                "state_updates": len(self.store.edt_states.list_all()),
                "at": _now(),
            },
        )
