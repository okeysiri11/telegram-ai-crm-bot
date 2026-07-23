"""AI financial intelligence — health score, recommendations, anomalies, NL reports."""

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
        self.insight_types = list(DEFAULT_CONFIG.rpt_ai_insight_types)

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
        iid = _id("rpt_ai")
        return self.store.rpt_ai_insights.save(
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

    def health_score(self, *, subject: str = "group", score: float = 0.82) -> dict[str, Any]:
        return self.insight(
            insight_type="financial_health",
            subject=subject,
            score=score,
            detail=f"Financial health score {score:.2f} for {subject}",
        )

    def nl_report(self, *, audience: str = "executive") -> dict[str, Any]:
        stmts = self.store.rpt_statements.count()
        kpis = self.store.rpt_kpis.count()
        forecasts = self.store.rpt_forecasts.count()
        narrative = (
            f"Executive financial report for {audience}: {stmts} statements, "
            f"{kpis} KPIs, {forecasts} forecasts. Review profitability and liquidity outlook."
        )
        return self.insight(
            insight_type="nl_report",
            subject=audience,
            score=0.88,
            detail=narrative,
        )

    def status(self) -> dict[str, Any]:
        return {"insights": self.store.rpt_ai_insights.count(), "types": self.insight_types}
