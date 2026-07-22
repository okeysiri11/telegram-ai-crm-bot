# Budget Engine — cost centers and budgets.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.finance.events import BudgetExceededEvent
from applications.port_erp.finance.models import Budget, CostCenter
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class BudgetEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def create_cost_center(self, center: CostCenter) -> CostCenter:
        if not center.code or not center.name:
            raise ValidationError("code and name are required")
        return self._store.cost_centers.save(center.cost_center_id, center)

    def list_cost_centers(self) -> list[CostCenter]:
        return self._store.cost_centers.list_all()

    def create_budget(self, budget: Budget) -> Budget:
        if not budget.name:
            raise ValidationError("name is required")
        if budget.amount < 0:
            raise ValidationError("amount must be non-negative")
        return self._store.budgets.save(budget.budget_id, budget)

    def list_budgets(self, *, company_id: str | None = None) -> list[Budget]:
        items = self._store.budgets.list_all()
        if company_id:
            items = [b for b in items if b.company_id == company_id]
        return items

    async def record_spend(self, budget_id: str, *, amount: float) -> Budget:
        budget = self._store.budgets.get(budget_id)
        if budget is None:
            raise NotFoundError("Budget", budget_id)
        if amount < 0:
            raise ValidationError("amount must be non-negative")
        budget.spent = round(budget.spent + amount, 2)
        saved = self._store.budgets.save(budget_id, budget)
        if saved.spent > saved.amount:
            await publish(
                BudgetExceededEvent(
                    budget_id=budget_id,
                    cost_center=saved.cost_center,
                    spent=saved.spent,
                    amount=saved.amount,
                )
            )
        return saved


budget_engine = BudgetEngine()
