
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

from applications.enterprise_hub.business_capabilities.strategy_alignment import StrategyAlignment


class StrategyAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.alignment = StrategyAlignment(self.store)

    def report(self) -> dict[str, Any]:
        alignments = self.store.ebc_alignments.list_all()
        avg = (
            round(sum(float(a.get("strategy_impact_score", 0)) for a in alignments) / len(alignments), 2)
            if alignments
            else 0.0
        )
        rid = _id("ebc_astrat")
        record = {
            "analytics_id": rid,
            "kind": "strategy",
            "alignments": len(alignments),
            "average_impact": avg,
            "strategic_risks": max(0, 5 - len(alignments)),
            "reported_at": _now(),
        }
        self.store.ebc_analytics.save(rid, record)
        return record
