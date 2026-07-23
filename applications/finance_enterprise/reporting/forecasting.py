"""Forecasting & scenario analysis — revenue/profit/cash/liquidity, sensitivity."""

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


class ReportingForecasting:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.forecast_kinds = list(DEFAULT_CONFIG.rpt_forecast_kinds)

    def forecast(
        self,
        *,
        kind: str,
        horizon_days: int = 90,
        projected: float = 0.0,
        confidence: float = 0.8,
        label: str = "",
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in self.forecast_kinds:
            raise ValidationError(f"kind must be one of {self.forecast_kinds}")
        fid = _id("rpt_fc")
        return self.store.rpt_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "kind": k,
                "horizon_days": int(horizon_days),
                "projected": float(projected),
                "confidence": max(0.0, min(1.0, float(confidence))),
                "label": label or k.replace("_", " "),
                "at": _now(),
            },
        )

    def scenario(
        self, *, name: str, base: float, uplift_pct: float = 0.0, detail: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        sid = _id("rpt_scn")
        result = round(float(base) * (1 + float(uplift_pct) / 100.0), 8)
        return self.store.rpt_scenarios.save(
            sid,
            {
                "scenario_id": sid,
                "name": name,
                "base": float(base),
                "uplift_pct": float(uplift_pct),
                "result": result,
                "detail": detail,
                "at": _now(),
            },
        )

    def sensitivity(
        self, *, driver: str, base: float, shock_pct: float, impact: float = 0.0
    ) -> dict[str, Any]:
        if not driver:
            raise ValidationError("driver required")
        sid = _id("rpt_sens")
        return self.store.rpt_sensitivity.save(
            sid,
            {
                "sensitivity_id": sid,
                "driver": driver,
                "base": float(base),
                "shock_pct": float(shock_pct),
                "impact": float(impact),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "forecasts": self.store.rpt_forecasts.count(),
            "scenarios": self.store.rpt_scenarios.count(),
            "sensitivity": self.store.rpt_sensitivity.count(),
            "kinds": self.forecast_kinds,
        }
