# Planning Engine — berth, crane, labor, equipment, yard, warehouse plans.

from __future__ import annotations

from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminal_operations.models import PlanType, TerminalPlan


class PlanningEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def create_plan(self, plan: TerminalPlan) -> TerminalPlan:
        if not plan.title:
            raise ValidationError("title is required")
        if not plan.terminal_id:
            raise ValidationError("terminal_id is required")
        return self._store.terminal_plans.save(plan.plan_id, plan)

    def get_plan(self, plan_id: str) -> TerminalPlan:
        plan = self._store.terminal_plans.get(plan_id)
        if plan is None:
            raise NotFoundError("TerminalPlan", plan_id)
        return plan

    def list_plans(
        self,
        *,
        terminal_id: str | None = None,
        plan_type: PlanType | None = None,
    ) -> list[TerminalPlan]:
        items = self._store.terminal_plans.list_all()
        if terminal_id:
            items = [p for p in items if p.terminal_id == terminal_id]
        if plan_type:
            items = [p for p in items if p.plan_type == plan_type]
        return items

    def activate(self, plan_id: str) -> TerminalPlan:
        plan = self.get_plan(plan_id)
        plan.status = "active"
        return self._store.terminal_plans.save(plan_id, plan)

    def complete(self, plan_id: str) -> TerminalPlan:
        plan = self.get_plan(plan_id)
        plan.status = "completed"
        return self._store.terminal_plans.save(plan_id, plan)

    def plan_types(self) -> list[str]:
        return [p.value for p in PlanType]


planning_engine = PlanningEngine()
