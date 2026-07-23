"""AI treasury intelligence — deviations, liquidity risk, anomalies, NL summary."""

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


class AITreasuryIntelligence:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.insight_types = list(DEFAULT_CONFIG.tr_ai_insight_types)

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
        iid = _id("tr_ai")
        return self.store.tr_ai_insights.save(
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
        pools = self.store.tr_pools.count()
        budgets = self.store.tr_budgets.count()
        forecasts = self.store.tr_forecasts.count()
        narrative = (
            f"Treasury summary for {audience}: {pools} cash pools, {budgets} budgets, "
            f"{forecasts} forecasts. Liquidity is monitored; prioritize variance remediation."
        )
        return self.insight(
            insight_type="nl_summary",
            subject=audience,
            score=0.86,
            detail=narrative,
        )

    def status(self) -> dict[str, Any]:
        return {"insights": self.store.tr_ai_insights.count(), "types": self.insight_types}
