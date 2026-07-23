"""Enterprise legal analytics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LegalAnalytics:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.kinds = list(DEFAULT_CONFIG.ei_analytics_kinds)

    def report(self, *, kind: str, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in self.kinds:
            raise ValidationError(f"kind must be one of {self.kinds}")
        defaults = {
            "case_success": {"win_rate": 0.62, "settled": 0.28, "loss_rate": 0.1},
            "court_performance": {"avg_days_to_ruling": 96, "favorable_rate": 0.55},
            "judge": {"judges_tracked": 24, "avg_plaintiff_favor": 0.48},
            "legal_cost": {"ytd_spend": 1_250_000, "budget_utilization": 0.71},
            "contract": {"pending": 14, "avg_cycle_days": 18, "high_risk": 3},
            "compliance": {"open_items": 9, "overdue": 2, "compliant_pct": 0.84},
            "risk_trend": {"score_30d": 58, "score_90d": 61, "direction": "stable"},
        }
        rid = _id("ei_anl")
        return self.store.ei_analytics.save(
            rid,
            {
                "report_id": rid,
                "kind": k,
                "metrics": metrics or defaults[k],
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"reports": self.store.ei_analytics.count(), "kinds": self.kinds}
