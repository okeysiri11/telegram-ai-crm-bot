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



class AnomalyAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        twins = self.store.edt_twins.list_all()
        anomalies = []
        for t in twins:
            st = t.get("state") or {}
            if st.get("anomaly") or st.get("status") == "error" or t.get("status") == "syncing":
                anomalies.append({"twin_id": t["twin_id"], "reason": st.get("anomaly") or t.get("status")})
        cons = self.store.edt_consistency.list_all()
        inconsistent = [c for c in cons if not c.get("consistent")]
        rid = _id("edt_anom")
        return self.store.edt_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "anomalies",
                "anomalies": anomalies,
                "anomaly_count": len(anomalies),
                "inconsistencies": len(inconsistent),
                "at": _now(),
            },
        )
