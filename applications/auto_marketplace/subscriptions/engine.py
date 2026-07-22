# Vehicle subscription plans.

from __future__ import annotations

from applications.auto_marketplace.fleet.models import SubscriptionPlan
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class SubscriptionEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_plan(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        if not plan.name:
            raise ValidationError("name is required")
        if not plan.includes:
            plan.includes = ["insurance", "maintenance", "roadside"]
        return self._store.subscription_plans.save(plan.plan_id, plan)

    def list_plans(self) -> list[SubscriptionPlan]:
        return self._store.subscription_plans.list_all()

    def metrics(self) -> dict:
        return {"subscription_plans": self._store.subscription_plans.count()}


subscription_engine = SubscriptionEngine()
