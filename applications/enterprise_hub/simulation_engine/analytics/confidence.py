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



class ConfidenceAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        decisions = self.store.esi_decisions.list_all()
        risks = self.store.esi_risks.list_all()
        avg_risk = (sum(r.get("overall", 0) for r in risks) / len(risks)) if risks else 0
        confidence = round(max(0.0, min(1.0, 1.0 - avg_risk)), 4)
        rid = _id("esi_conf")
        return self.store.esi_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "confidence",
                "decision_count": len(decisions),
                "avg_risk": avg_risk,
                "confidence": confidence,
                "at": _now(),
            },
        )
