"""Business intelligence — KPIs, revenue/expense/margin/profitability/trend/variance."""

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


class BusinessIntelligence:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.analytic_types = list(DEFAULT_CONFIG.rpt_analytic_types)
        self.kpi_types = list(DEFAULT_CONFIG.rpt_kpi_types)

    def register_kpi(
        self, *, name: str, kpi_type: str = "margin", value: float = 0.0, unit: str = "%"
    ) -> dict[str, Any]:
        kt = kpi_type.lower().strip()
        if kt not in self.kpi_types:
            raise ValidationError(f"kpi_type must be one of {self.kpi_types}")
        if not name:
            raise ValidationError("name required")
        kid = _id("rpt_kpi")
        return self.store.rpt_kpis.save(
            kid,
            {
                "kpi_id": kid,
                "name": name,
                "kpi_type": kt,
                "value": float(value),
                "unit": unit,
                "at": _now(),
            },
        )

    def analyze(
        self,
        *,
        analytic_type: str,
        subject: str,
        value: float = 0.0,
        prior: float = 0.0,
        detail: str = "",
    ) -> dict[str, Any]:
        at = analytic_type.lower().strip()
        if at not in self.analytic_types:
            raise ValidationError(f"analytic_type must be one of {self.analytic_types}")
        if not subject:
            raise ValidationError("subject required")
        change = round(float(value) - float(prior), 8)
        pct = round((change / float(prior)) * 100, 4) if prior else 0.0
        aid = _id("rpt_bi")
        return self.store.rpt_analytics.save(
            aid,
            {
                "analytic_id": aid,
                "analytic_type": at,
                "subject": subject,
                "value": float(value),
                "prior": float(prior),
                "change": change,
                "change_pct": pct,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "kpis": self.store.rpt_kpis.count(),
            "analytics": self.store.rpt_analytics.count(),
            "kpi_types": self.kpi_types,
            "analytic_types": self.analytic_types,
        }
