"""Enterprise consolidation — multi-company, IC elimination, group performance."""

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


class EnterpriseConsolidation:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.consolidation_types = list(DEFAULT_CONFIG.rpt_consolidation_types)

    def consolidate(
        self,
        *,
        consolidation_type: str,
        label: str,
        companies: list[str] | None = None,
        amount: float = 0.0,
        eliminated: float = 0.0,
        detail: str = "",
    ) -> dict[str, Any]:
        ct = consolidation_type.lower().strip()
        if ct not in self.consolidation_types:
            raise ValidationError(f"consolidation_type must be one of {self.consolidation_types}")
        if not label:
            raise ValidationError("label required")
        cid = _id("rpt_con")
        gross = float(amount)
        elim = float(eliminated)
        return self.store.rpt_consolidations.save(
            cid,
            {
                "consolidation_id": cid,
                "consolidation_type": ct,
                "label": label,
                "companies": companies or [],
                "gross_amount": gross,
                "eliminated": elim,
                "consolidated_amount": round(gross - elim, 8),
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "consolidations": self.store.rpt_consolidations.count(),
            "types": self.consolidation_types,
        }
