# Strategic planning — company/department objectives and horizons.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store
from ecosystem.workforce.events import ObjectiveCompletedEvent, PlanningUpdatedEvent
from ecosystem.workforce.models import DepartmentType, Objective, PlanHorizon, WorkPlan


class PlanningService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def set_objective(
        self,
        title: str,
        *,
        horizon: PlanHorizon = PlanHorizon.COMPANY,
        department_type: DepartmentType | None = None,
        target_metric: str = "",
        target_value: float = 100.0,
        owner_role: str = "",
    ) -> Objective:
        if not title:
            raise ValidationError("title is required")
        objective = Objective(
            title=title,
            horizon=horizon,
            department_type=department_type,
            target_metric=target_metric or "progress",
            target_value=target_value,
            owner_role=owner_role,
        )
        self._store.objectives.save(objective.objective_id, objective)
        return objective

    async def update_progress(self, objective_id: str, current_value: float) -> Objective:
        objective = self.get_objective(objective_id)
        objective.current_value = current_value
        if objective.target_value and current_value >= objective.target_value:
            objective.status = "completed"
            await publish(
                ObjectiveCompletedEvent(
                    objective_id=objective_id,
                    title=objective.title,
                    horizon=objective.horizon.value,
                )
            )
        self._store.objectives.save(objective_id, objective)
        return objective

    async def create_plan(
        self,
        title: str,
        horizon: PlanHorizon,
        items: list[dict[str, Any]],
        *,
        department_type: DepartmentType | None = None,
    ) -> WorkPlan:
        plan = WorkPlan(
            title=title,
            horizon=horizon,
            department_type=department_type,
            items=items,
        )
        self._store.work_plans.save(plan.plan_id, plan)
        await publish(PlanningUpdatedEvent(plan_id=plan.plan_id, horizon=horizon.value, title=title))
        return plan

    async def update_plan(self, plan_id: str, *, items: list[dict[str, Any]] | None = None, status: str = "") -> WorkPlan:
        plan = self.get_plan(plan_id)
        if items is not None:
            plan.items = items
        if status:
            plan.status = status
        plan.updated_at = time.time()
        self._store.work_plans.save(plan_id, plan)
        await publish(PlanningUpdatedEvent(plan_id=plan_id, horizon=plan.horizon.value, title=plan.title))
        return plan

    def quarterly_plan(self, title: str, items: list[dict[str, Any]]) -> WorkPlan:
        # sync create wrapper used by tests/engine — actually async create_plan is preferred
        plan = WorkPlan(title=title, horizon=PlanHorizon.QUARTERLY, items=items)
        self._store.work_plans.save(plan.plan_id, plan)
        return plan

    def weekly_plan(self, title: str, items: list[dict[str, Any]], *, department_type: DepartmentType | None = None) -> WorkPlan:
        plan = WorkPlan(title=title, horizon=PlanHorizon.WEEKLY, department_type=department_type, items=items)
        self._store.work_plans.save(plan.plan_id, plan)
        return plan

    def daily_execution(self, title: str, items: list[dict[str, Any]]) -> WorkPlan:
        plan = WorkPlan(title=title, horizon=PlanHorizon.DAILY, items=items)
        self._store.work_plans.save(plan.plan_id, plan)
        return plan

    def performance_report(self) -> dict[str, Any]:
        objectives = self._store.objectives.list_all()
        plans = self._store.work_plans.list_all()
        completed = [o for o in objectives if o.status == "completed"]
        return {
            "objectives_total": len(objectives),
            "objectives_completed": len(completed),
            "plans_active": len([p for p in plans if p.status == "active"]),
            "avg_progress": round(
                sum((o.current_value / o.target_value) if o.target_value else 0 for o in objectives) / len(objectives),
                2,
            )
            if objectives
            else 0,
            "objectives": [o.to_dict() for o in objectives],
        }

    def get_objective(self, objective_id: str) -> Objective:
        objective = self._store.objectives.get(objective_id)
        if objective is None:
            raise NotFoundError("Objective", objective_id)
        return objective

    def get_plan(self, plan_id: str) -> WorkPlan:
        plan = self._store.work_plans.get(plan_id)
        if plan is None:
            raise NotFoundError("WorkPlan", plan_id)
        return plan

    def list_objectives(self, *, horizon: PlanHorizon | None = None) -> list[Objective]:
        objectives = self._store.objectives.list_all()
        if horizon:
            objectives = [o for o in objectives if o.horizon == horizon]
        return objectives

    def list_plans(self, *, horizon: PlanHorizon | None = None) -> list[WorkPlan]:
        plans = self._store.work_plans.list_all()
        if horizon:
            plans = [p for p in plans if p.horizon == horizon]
        return plans


planning_service = PlanningService()
