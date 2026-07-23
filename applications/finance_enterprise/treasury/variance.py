"""Variance analysis — budget vs actual, KPIs."""

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


class VarianceAnalysis:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.variance_types = list(DEFAULT_CONFIG.tr_variance_types)

    def analyze(
        self,
        *,
        variance_type: str,
        budget: float,
        actual: float,
        subject: str = "",
    ) -> dict[str, Any]:
        vt = variance_type.lower().strip()
        if vt not in self.variance_types:
            raise ValidationError(f"variance_type must be one of {self.variance_types}")
        b = float(budget)
        a = float(actual)
        variance = round(a - b, 6)
        pct = round((variance / b) * 100, 2) if b else 0.0
        vid = _id("tr_var")
        return self.store.tr_variances.save(
            vid,
            {
                "variance_id": vid,
                "variance_type": vt,
                "subject": subject or vt,
                "budget": b,
                "actual": a,
                "variance": variance,
                "variance_pct": pct,
                "at": _now(),
            },
        )

    def kpi(
        self, *, name: str, value: float, target: float = 0.0, unit: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        kid = _id("tr_kpi")
        return self.store.tr_kpis.save(
            kid,
            {
                "kpi_id": kid,
                "name": name,
                "value": float(value),
                "target": float(target),
                "unit": unit,
                "delta": round(float(value) - float(target), 6),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "variances": self.store.tr_variances.count(),
            "kpis": self.store.tr_kpis.count(),
            "types": self.variance_types,
        }
