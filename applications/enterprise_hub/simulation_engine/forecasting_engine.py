from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.simulation_engine.models import FORECAST_TARGETS


class ForecastingEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def forecast(
        self,
        *,
        target: str,
        horizon: str = "90d",
        baseline: float = 100.0,
        growth_pct: float = 5.0,
    ) -> dict[str, Any]:
        if target not in FORECAST_TARGETS:
            raise ValidationError(f"invalid forecast target: {target}")
        points = []
        value = float(baseline)
        for step in range(1, 5):
            value = value * (1 + growth_pct / 100)
            points.append({"step": step, "value": round(value, 2)})
        fid = _id("esi_fc")
        return self.store.esi_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "target": target,
                "horizon": horizon,
                "baseline": baseline,
                "growth_pct": growth_pct,
                "series": points,
                "final": points[-1]["value"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"forecasts": len(self.store.esi_forecasts.list_all())}
