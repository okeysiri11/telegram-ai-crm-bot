"""Regulatory forecasting — amendments, impact, alerts, AI reports."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


FORECAST_ACTIONS = (
    "upcoming_change",
    "amendment",
    "industry_impact",
    "compliance_forecast",
    "legislative_alert",
    "ai_impact_report",
)


class RegulatoryForecasting:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def register(
        self,
        *,
        action: str,
        title: str,
        impact: str = "medium",
        industry: str = "",
        detail: str = "",
    ) -> dict[str, Any]:
        a = action.lower().strip()
        if a not in FORECAST_ACTIONS:
            raise ValidationError(f"action must be one of {list(FORECAST_ACTIONS)}")
        if not title:
            raise ValidationError("title required")
        fid = _id("ei_reg")
        return self.store.ei_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "action": a,
                "title": title,
                "impact": impact,
                "industry": industry or "general",
                "detail": detail or f"{a.replace('_', ' ')}: {title}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"forecasts": self.store.ei_forecasts.count(), "actions": list(FORECAST_ACTIONS)}
