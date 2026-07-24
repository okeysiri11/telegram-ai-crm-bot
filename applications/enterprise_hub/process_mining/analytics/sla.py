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



class SlaAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self, *, process_id: str) -> dict[str, Any]:
        confs = [c for c in self.store.epm_conformance.list_all() if c.get("process_id") == process_id]
        breaches = 0
        for c in confs:
            breaches += sum(1 for v in c.get("violations") or [] if v.get("kind") == "sla_breach")
        sid = _id("epm_sla")
        return self.store.epm_analytics.save(
            sid,
            {
                "analytics_id": sid,
                "kind": "sla",
                "process_id": process_id,
                "breaches": breaches,
                "on_time_pct": round(max(0, 100 - breaches * 12), 2),
                "at": _now(),
            },
        )
