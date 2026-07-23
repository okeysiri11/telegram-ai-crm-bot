"""Financial performance analysis — revenue, expense, profitability, margins, WC."""

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


class PerformanceAnalysis:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.analysis_types = list(DEFAULT_CONFIG.cfo_performance_types)

    def analyze(
        self,
        *,
        analysis_type: str,
        subject: str,
        value: float = 0.0,
        prior: float = 0.0,
        detail: str = "",
    ) -> dict[str, Any]:
        at = analysis_type.lower().strip()
        if at not in self.analysis_types:
            raise ValidationError(f"analysis_type must be one of {self.analysis_types}")
        if not subject:
            raise ValidationError("subject required")
        change = round(float(value) - float(prior), 8)
        aid = _id("cfo_perf")
        return self.store.cfo_performance.save(
            aid,
            {
                "analysis_id": aid,
                "analysis_type": at,
                "subject": subject,
                "value": float(value),
                "prior": float(prior),
                "change": change,
                "detail": detail or f"{at.replace('_', ' ')} for {subject}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "analyses": self.store.cfo_performance.count(),
            "types": self.analysis_types,
        }
