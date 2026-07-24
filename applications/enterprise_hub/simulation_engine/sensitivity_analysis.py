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




class SensitivityAnalysis:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def analyze(
        self,
        *,
        parameters: dict[str, float] | None = None,
        outcome_key: str = "profit",
    ) -> dict[str, Any]:
        params = dict(parameters or {"fuel_cost": 1.0, "demand": 1.0, "wage_rate": 1.0})
        if not params:
            raise ValidationError("parameters required")
        # chain: fuel -> transport -> product_cost -> profit
        influences = []
        for name, base in params.items():
            delta = 0.1
            up = base * (1 + delta)
            # simplified elasticity by parameter name
            elasticity = 0.8 if "fuel" in name or "cost" in name else 0.4 if "demand" in name else 0.3
            impact = round(elasticity * delta * 100, 2)
            chain = []
            if "fuel" in name:
                chain = ["fuel_cost", "transport_cost", "product_cost", outcome_key]
            else:
                chain = [name, outcome_key]
            influences.append({"parameter": name, "elasticity": elasticity, "impact_pct": impact, "chain": chain})
        influences.sort(key=lambda x: x["impact_pct"], reverse=True)
        sid = _id("esi_sens")
        return self.store.esi_sensitivity.save(
            sid,
            {
                "analysis_id": sid,
                "outcome_key": outcome_key,
                "parameters": params,
                "influences": influences,
                "top_driver": influences[0]["parameter"] if influences else None,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"analyses": len(self.store.esi_sensitivity.list_all())}
