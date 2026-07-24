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



from applications.enterprise_hub.simulation_engine.optimization.inventory_optimizer import InventoryOptimizer
from applications.enterprise_hub.simulation_engine.optimization.resource_optimizer import ResourceOptimizer
from applications.enterprise_hub.simulation_engine.optimization.route_optimizer import RouteOptimizer
from applications.enterprise_hub.simulation_engine.optimization.schedule_optimizer import ScheduleOptimizer
from applications.enterprise_hub.simulation_engine.optimization.workforce_optimizer import WorkforceOptimizer


class OptimizationEngine:
    """Sprint map optimization_engine.py — lives in optimization/ to avoid package clash."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.resources = ResourceOptimizer(self.store)
        self.schedule = ScheduleOptimizer(self.store)
        self.routes = RouteOptimizer(self.store)
        self.inventory = InventoryOptimizer(self.store)
        self.workforce = WorkforceOptimizer(self.store)

    def optimize_all(self, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {"baseline": 100}
        results = [
            self.resources.optimize(objective="minimize_cost", constraints=ctx),
            self.schedule.optimize(objective="minimize_time", constraints=ctx),
            self.routes.optimize(objective="minimize_cost", constraints=ctx),
            self.inventory.optimize(objective="minimize_cost", constraints=ctx),
            self.workforce.optimize(objective="maximize_efficiency", constraints=ctx),
        ]
        bid = _id("esi_batch")
        return self.store.esi_opt_batches.save(
            bid,
            {
                "batch_id": bid,
                "optimization_ids": [r["optimization_id"] for r in results],
                "total_gain": sum(r.get("gain", 0) for r in results),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "optimizations": len(self.store.esi_optimizations.list_all()),
            "batches": len(self.store.esi_opt_batches.list_all()),
        }
