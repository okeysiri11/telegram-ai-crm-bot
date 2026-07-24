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




class ProcessSimulator:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def simulate(
        self,
        *,
        process_id: str,
        optimization_id: str | None = None,
        cases: int = 100,
    ) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        if cases < 1:
            raise ValidationError("cases must be positive")
        base_hours = 4 * len(process.get("steps") or [])
        reduction = 0.0
        if optimization_id:
            opt = self.store.epm_optimizations.get(optimization_id)
            if opt:
                reduction = float((opt.get("expected_effect") or {}).get("duration_reduction_pct", 0)) / 100
        simulated = round(base_hours * (1 - reduction), 2)
        sid = _id("epm_sim")
        return self.store.epm_simulations.save(
            sid,
            {
                "simulation_id": sid,
                "process_id": process_id,
                "optimization_id": optimization_id,
                "cases": cases,
                "baseline_hours": base_hours,
                "simulated_hours": simulated,
                "improvement_pct": round(reduction * 100, 2),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"simulations": len(self.store.epm_simulations.list_all())}
