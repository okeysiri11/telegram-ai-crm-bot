"""Executive reporting — daily/weekly/monthly/board briefings and NL reports."""

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


class ExecutiveReporting:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.report_types = list(DEFAULT_CONFIG.cfo_report_types)

    def report(
        self,
        *,
        report_type: str,
        audience: str = "executive",
        narrative: str = "",
        period: str = "",
    ) -> dict[str, Any]:
        rt = report_type.lower().strip()
        if rt not in self.report_types:
            raise ValidationError(f"report_type must be one of {self.report_types}")
        rid = _id("cfo_rpt")
        text = narrative or (
            f"{rt.replace('_', ' ').title()} for {audience}"
            + (f" ({period})" if period else "")
            + f": {self.store.cfo_recommendations.count()} recommendations, "
            f"{self.store.cfo_risks.count()} risks monitored."
        )
        return self.store.cfo_reports.save(
            rid,
            {
                "report_id": rid,
                "report_type": rt,
                "audience": audience,
                "period": period,
                "narrative": text,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"reports": self.store.cfo_reports.count(), "types": self.report_types}
