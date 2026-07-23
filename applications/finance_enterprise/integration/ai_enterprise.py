"""AI enterprise finance — monitoring, anomalies, recommendations, health, NL reports."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIEnterpriseFinance:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.insight_types = list(DEFAULT_CONFIG.int_ai_insight_types)

    def insight(
        self,
        *,
        insight_type: str,
        subject: str,
        score: float = 0.7,
        detail: str = "",
    ) -> dict[str, Any]:
        it = insight_type.lower().strip()
        if it not in self.insight_types:
            raise ValidationError(f"insight_type must be one of {self.insight_types}")
        if not subject:
            raise ValidationError("subject required")
        iid = _id("int_ai")
        return self.store.int_ai_insights.save(
            iid,
            {
                "insight_id": iid,
                "insight_type": it,
                "subject": subject,
                "score": max(0.0, min(1.0, float(score))),
                "detail": detail or f"{it.replace('_', ' ')} for {subject}",
                "at": _now(),
            },
        )

    def health_score(self, *, subject: str = "enterprise", score: float = 0.86) -> dict[str, Any]:
        return self.insight(
            insight_type="enterprise_health",
            subject=subject,
            score=score,
            detail=f"Enterprise financial health {score:.2f} for {subject}",
        )

    def nl_report(self, *, audience: str = "executive") -> dict[str, Any]:
        events = self.store.int_events.count()
        ops = self.store.int_operations.count()
        platforms = len({o["platform"] for o in self.store.int_operations.list_all()})
        narrative = (
            f"Enterprise finance report for {audience}: {events} events, "
            f"{ops} operations across {platforms} platforms. Monitor anomalies and cash dependencies."
        )
        return self.insight(
            insight_type="nl_report",
            subject=audience,
            score=0.9,
            detail=narrative,
        )

    def status(self) -> dict[str, Any]:
        return {"insights": self.store.int_ai_insights.count(), "types": self.insight_types}
