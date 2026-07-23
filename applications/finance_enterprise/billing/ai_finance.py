"""AI financial intelligence — predictions, recommendations, anomalies, NL summaries."""

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


class AIFinancialIntelligence:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.insight_types = list(DEFAULT_CONFIG.bil_ai_insight_types)

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
        iid = _id("bil_ai")
        return self.store.bil_ai_insights.save(
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

    def nl_summary(self, *, audience: str = "executive") -> dict[str, Any]:
        inv = self.store.bil_invoices.count()
        ar = self.store.bil_receivables.count()
        ap = self.store.bil_bills.count()
        narrative = (
            f"Billing summary for {audience}: {inv} invoices, {ar} receivables, "
            f"{ap} payables tracked. Focus collections on overdue items and monitor cash forecast."
        )
        return self.insight(
            insight_type="nl_summary",
            subject=audience,
            score=0.88,
            detail=narrative,
        )

    def status(self) -> dict[str, Any]:
        return {"insights": self.store.bil_ai_insights.count(), "types": self.insight_types}
