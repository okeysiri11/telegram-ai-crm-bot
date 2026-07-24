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



from applications.enterprise_hub.simulation_engine.models import RISK_KINDS


class RiskEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def assess(
        self,
        *,
        scenario_id: str | None = None,
        exposures: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        exp = {k: 0.2 for k in RISK_KINDS}
        if exposures:
            exp.update({k: float(v) for k, v in exposures.items() if k in RISK_KINDS})
        critical = [k for k, v in exp.items() if v >= 0.6]
        overall = round(sum(exp.values()) / len(exp), 4)
        rid = _id("esi_risk")
        return self.store.esi_risks.save(
            rid,
            {
                "risk_id": rid,
                "scenario_id": scenario_id,
                "exposures": exp,
                "overall": overall,
                "critical": critical,
                "dependencies": ["digital_twin", "data_fabric", "event_bus"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        items = self.store.esi_risks.list_all()
        return {"assessments": len(items), "avg_overall": (sum(i.get("overall", 0) for i in items) / len(items)) if items else 0}
