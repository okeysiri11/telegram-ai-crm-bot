# Optimization Engine — facade over berth, yard, resource AI planners.

from __future__ import annotations

from applications.port_erp.berth_scheduler.engine import BerthPlanningEngine, berth_planning_engine
from applications.port_erp.digital_twin.models import OptimizationPlan
from applications.port_erp.resource_manager.engine import PortResourceEngine, port_resource_engine
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.yard_optimizer.engine import YardOptimizationEngine, yard_optimization_engine


class OptimizationEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        berths: BerthPlanningEngine | None = None,
        yard: YardOptimizationEngine | None = None,
        resources: PortResourceEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self.berths = berths or berth_planning_engine
        self.yard = yard or yard_optimization_engine
        self.resources = resources or port_resource_engine

    async def run_all(self, *, vessel_id: str = "", terminal_id: str = "") -> list[OptimizationPlan]:
        plans = [
            await self.berths.allocate(vessel_id=vessel_id, prefer_terminal_id=terminal_id),
            await self.yard.optimize_flow(terminal_id=terminal_id),
            await self.resources.balance(),
        ]
        return plans

    def list_plans(self) -> list[OptimizationPlan]:
        return sorted(self._store.optimization_plans.list_all(), key=lambda p: p.created_at, reverse=True)


optimization_engine = OptimizationEngine()
