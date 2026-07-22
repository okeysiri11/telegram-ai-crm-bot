# Berth Planning Engine — AI berth allocation suggestions.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.digital_twin.events import OptimizationProposedEvent
from applications.port_erp.digital_twin.models import OptimizationPlan
from applications.port_erp.shared.store import PortStore, port_store


class BerthPlanningEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    async def allocate(self, *, vessel_id: str = "", prefer_terminal_id: str = "") -> OptimizationPlan:
        available = [
            b
            for b in self._store.berths.list_all()
            if getattr(b, "status", "available") == "available"
            and (not prefer_terminal_id or b.terminal_id == prefer_terminal_id)
        ]
        actions = []
        score = 0.5
        if available:
            berth = available[0]
            actions.append(
                {
                    "action": "assign_berth",
                    "berth_id": berth.berth_id,
                    "vessel_id": vessel_id,
                    "terminal_id": berth.terminal_id,
                }
            )
            score = 0.9 if prefer_terminal_id else 0.75
        else:
            actions.append({"action": "queue_vessel", "vessel_id": vessel_id, "reason": "no_berth"})
            score = 0.35

        plan = OptimizationPlan(
            plan_type="berth_allocation",
            title="Berth allocation plan",
            actions=actions,
            score=score,
        )
        saved = self._store.optimization_plans.save(plan.plan_id, plan)
        await publish(
            OptimizationProposedEvent(
                plan_id=saved.plan_id, plan_type=saved.plan_type, score=saved.score
            )
        )
        return saved


berth_planning_engine = BerthPlanningEngine()
