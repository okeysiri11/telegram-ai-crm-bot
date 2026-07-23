"""Forecasting — cash/revenue/expense/liquidity, scenarios, sensitivity."""

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


class Forecasting:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.forecast_kinds = list(DEFAULT_CONFIG.tr_forecast_kinds)

    def forecast(
        self,
        *,
        kind: str,
        horizon_days: int = 90,
        projected: float = 0.0,
        narrative: str = "",
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in self.forecast_kinds:
            raise ValidationError(f"kind must be one of {self.forecast_kinds}")
        fid = _id("tr_fc")
        return self.store.tr_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "kind": k,
                "horizon_days": max(1, int(horizon_days)),
                "projected": float(projected),
                "narrative": narrative or f"{k.replace('_', ' ').title()} forecast",
                "at": _now(),
            },
        )

    def scenario(
        self, *, name: str, base_amount: float, uplift_pct: float = 0.0
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("scenario name required")
        sid = _id("tr_scn")
        base = float(base_amount)
        uplift = float(uplift_pct)
        return self.store.tr_scenarios.save(
            sid,
            {
                "scenario_id": sid,
                "name": name,
                "base_amount": base,
                "uplift_pct": uplift,
                "projected": round(base * (1 + uplift / 100.0), 6),
                "at": _now(),
            },
        )

    def sensitivity(
        self, *, variable: str, low: float, base: float, high: float
    ) -> dict[str, Any]:
        if not variable:
            raise ValidationError("variable required")
        sid = _id("tr_sens")
        return self.store.tr_sensitivity.save(
            sid,
            {
                "sensitivity_id": sid,
                "variable": variable,
                "low": float(low),
                "base": float(base),
                "high": float(high),
                "spread": round(float(high) - float(low), 6),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "forecasts": self.store.tr_forecasts.count(),
            "scenarios": self.store.tr_scenarios.count(),
            "sensitivity": self.store.tr_sensitivity.count(),
            "kinds": self.forecast_kinds,
        }
