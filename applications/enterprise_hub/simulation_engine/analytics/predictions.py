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



class PredictionAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        forecasts = self.store.esi_forecasts.list_all()
        mc = self.store.esi_monte_carlo.list_all()
        rid = _id("esi_pred")
        return self.store.esi_analytics.save(
            rid,
            {
                "analytics_id": rid,
                "kind": "predictions",
                "forecast_count": len(forecasts),
                "monte_carlo_count": len(mc),
                "avg_forecast_final": (sum(f.get("final", 0) for f in forecasts) / len(forecasts)) if forecasts else 0,
                "at": _now(),
            },
        )
