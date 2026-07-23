"""Management reporting — department, project, cost center, BU, budget vs actual."""

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


class ManagementReporting:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.report_types = list(DEFAULT_CONFIG.rpt_management_types)

    def generate(
        self,
        *,
        report_type: str,
        subject: str,
        period: str = "",
        budget: float = 0.0,
        actual: float = 0.0,
        detail: str = "",
    ) -> dict[str, Any]:
        rt = report_type.lower().strip()
        if rt not in self.report_types:
            raise ValidationError(f"report_type must be one of {self.report_types}")
        if not subject:
            raise ValidationError("subject required")
        variance = round(float(actual) - float(budget), 8)
        rid = _id("rpt_mgmt")
        return self.store.rpt_management.save(
            rid,
            {
                "report_id": rid,
                "report_type": rt,
                "subject": subject,
                "period": period,
                "budget": float(budget),
                "actual": float(actual),
                "variance": variance,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "reports": self.store.rpt_management.count(),
            "types": self.report_types,
        }
