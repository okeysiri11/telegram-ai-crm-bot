# Statistics service — aggregate computations.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class StatisticsService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def summary(self) -> dict[str, Any]:
        payments = [p.amount for p in self._store.finance_payments.list_all() if p.status == "completed"]
        return {
            "count_payments": len(payments),
            "sum_payments": round(sum(payments), 2),
            "mean_payment": round(sum(payments) / max(len(payments), 1), 2),
            "max_payment": round(max(payments), 2) if payments else 0,
            "min_payment": round(min(payments), 2) if payments else 0,
            "total_leads": self._store.crm_leads.count(),
            "total_deals": self._store.crm_deals.count(),
            "total_customers": self._store.customer_profiles.count(),
        }

    def distribution(self, field: str = "deal_stage") -> dict[str, int]:
        if field == "deal_stage":
            dist: dict[str, int] = {}
            for deal in self._store.crm_deals.list_all():
                dist[deal.stage.value] = dist.get(deal.stage.value, 0) + 1
            return dist
        return {}


statistics_service = StatisticsService()
