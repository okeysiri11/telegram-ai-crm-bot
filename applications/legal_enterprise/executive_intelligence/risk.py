"""Risk intelligence — enterprise, department, counterparty, forecasts."""

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


def _band(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


class RiskIntelligence:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.score_types = list(DEFAULT_CONFIG.ei_risk_score_types)

    def score(
        self,
        *,
        score_type: str,
        subject: str,
        value: float,
        detail: str = "",
    ) -> dict[str, Any]:
        st = score_type.lower().strip()
        if st not in self.score_types:
            raise ValidationError(f"score_type must be one of {self.score_types}")
        if not subject:
            raise ValidationError("subject required")
        val = max(0.0, min(100.0, float(value)))
        rid = _id("ei_risk")
        return self.store.ei_risks.save(
            rid,
            {
                "risk_id": rid,
                "score_type": st,
                "subject": subject,
                "score": val,
                "band": _band(val),
                "detail": detail,
                "at": _now(),
            },
        )

    def forecast(
        self,
        *,
        forecast_type: str,
        horizon_days: int = 90,
        projected_score: float = 55.0,
        narrative: str = "",
    ) -> dict[str, Any]:
        ft = forecast_type.lower().strip()
        allowed = ("litigation", "compliance", "regulatory_exposure", "contract_trend")
        if ft not in allowed:
            raise ValidationError(f"forecast_type must be one of {list(allowed)}")
        fid = _id("ei_rf")
        proj = max(0.0, min(100.0, float(projected_score)))
        return self.store.ei_risk_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "forecast_type": ft,
                "horizon_days": max(1, int(horizon_days)),
                "projected_score": proj,
                "band": _band(proj),
                "narrative": narrative or f"{ft.replace('_', ' ').title()} forecast over {horizon_days} days",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "scores": self.store.ei_risks.count(),
            "forecasts": self.store.ei_risk_forecasts.count(),
            "score_types": self.score_types,
        }
