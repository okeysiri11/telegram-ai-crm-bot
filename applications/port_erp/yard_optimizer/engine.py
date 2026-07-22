# Yard Optimization Engine — container flow / density balancing.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.digital_twin.events import OptimizationProposedEvent
from applications.port_erp.digital_twin.models import OptimizationPlan
from applications.port_erp.shared.store import PortStore, port_store


class YardOptimizationEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    async def optimize_flow(self, *, terminal_id: str = "") -> OptimizationPlan:
        slots = self._store.yard_slots.list_all()
        if terminal_id:
            slots = [s for s in slots if s.terminal_id == terminal_id]
        occupied = [s for s in slots if getattr(s.status, "value", "") == "occupied"]
        empty = [s for s in slots if getattr(s.status, "value", "") == "empty"]
        density = (len(occupied) / len(slots)) if slots else 0.0
        actions: list[dict] = []
        if density > 0.8 and empty:
            actions.append(
                {
                    "action": "relocate_hot_containers",
                    "from_slots": len(occupied),
                    "target_empty": empty[0].slot_id,
                }
            )
        if density < 0.3 and occupied:
            actions.append({"action": "compact_stacks", "occupied": len(occupied)})
        if not actions:
            actions.append({"action": "maintain", "density": round(density, 3)})

        plan = OptimizationPlan(
            plan_type="container_flow",
            title="Yard container flow optimization",
            actions=actions,
            score=round(1.0 - abs(0.65 - density), 3),
        )
        saved = self._store.optimization_plans.save(plan.plan_id, plan)
        await publish(
            OptimizationProposedEvent(
                plan_id=saved.plan_id, plan_type=saved.plan_type, score=saved.score
            )
        )
        return saved


yard_optimization_engine = YardOptimizationEngine()
