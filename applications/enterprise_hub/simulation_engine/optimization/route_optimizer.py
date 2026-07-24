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


class RouteOptimizer:
    KIND = "routes"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def optimize(self, *, objective: str = "minimize_cost", constraints: dict[str, Any] | None = None) -> dict[str, Any]:
        oid = _id("esi_opt")
        cons = constraints or {}
        baseline = float(cons.get("baseline", 100))
        gain = round(baseline * 0.12, 2)
        return self.store.esi_optimizations.save(
            oid,
            {
                "optimization_id": oid,
                "kind": self.KIND,
                "objective": objective,
                "constraints": cons,
                "baseline": baseline,
                "improved": round(baseline - gain, 2) if "min" in objective else round(baseline + gain, 2),
                "gain": gain,
                "recommendation": f"adjust {self.KIND} for {objective}",
                "at": _now(),
            },
        )
