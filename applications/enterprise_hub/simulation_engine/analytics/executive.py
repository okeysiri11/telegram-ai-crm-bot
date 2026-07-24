"""Executive reporting for Decision Analytics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ExecutiveReporting:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        decisions = self.store.esi_decisions.list_all()
        risks = self.store.esi_risks.list_all()
        forecasts = self.store.esi_forecasts.list_all()
        recs = self.store.esi_recommendations.list_all()
        potential_profit = 0.0
        potential_loss = 0.0
        for d in decisions:
            for opt in d.get("ranked") or []:
                scores = opt.get("scores") or {}
                potential_profit += float(scores.get("profit", 0))
                potential_loss += float(100 - scores.get("risk", 50))
        rid = _id("esi_exec")
        return self.store.esi_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "executive",
                "decisions_reviewed": len(decisions),
                "forecasts": len(forecasts),
                "ai_recommendations": len(recs),
                "potential_profit_index": round(potential_profit, 2),
                "potential_loss_index": round(potential_loss, 2),
                "risk_level": (sum(r.get("overall", 0) for r in risks) / len(risks)) if risks else 0,
                "at": _now(),
            },
        )
