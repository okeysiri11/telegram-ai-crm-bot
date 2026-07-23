"""Risk intelligence — liquidity, credit, cash flow, budget deviation, stability."""

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


class RiskIntelligence:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.risk_types = list(DEFAULT_CONFIG.cfo_risk_types)

    def assess(
        self,
        *,
        risk_type: str,
        subject: str,
        score: float = 0.5,
        mitigation: str = "",
        detail: str = "",
    ) -> dict[str, Any]:
        rt = risk_type.lower().strip()
        if rt not in self.risk_types:
            raise ValidationError(f"risk_type must be one of {self.risk_types}")
        if not subject:
            raise ValidationError("subject required")
        rid = _id("cfo_risk")
        severity = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
        return self.store.cfo_risks.save(
            rid,
            {
                "risk_id": rid,
                "risk_type": rt,
                "subject": subject,
                "score": max(0.0, min(1.0, float(score))),
                "severity": severity,
                "mitigation": mitigation or f"Mitigate {rt.replace('_', ' ')} for {subject}",
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"risks": self.store.cfo_risks.count(), "types": self.risk_types}
