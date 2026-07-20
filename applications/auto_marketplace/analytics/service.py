# AnalyticsService — marketplace metrics and reporting.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AnalyticsService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def dashboard_metrics(self) -> dict[str, Any]:
        return {
            "vehicles": self._store.vehicles.count(),
            "dealers": self._store.dealers.count(),
            "customers": self._store.customers.count(),
            "leads": self._store.leads.count(),
            "deals": self._store.deals.count(),
            "payments": self._store.payments.count(),
            "deliveries": self._store.deliveries.count(),
        }

    def sales_pipeline(self) -> dict[str, Any]:
        leads = self._store.leads.list_all()
        deals = self._store.deals.list_all()
        by_lead_status: dict[str, int] = {}
        for lead in leads:
            by_lead_status[lead.status.value] = by_lead_status.get(lead.status.value, 0) + 1
        by_deal_status: dict[str, int] = {}
        for deal in deals:
            by_deal_status[deal.status.value] = by_deal_status.get(deal.status.value, 0) + 1
        return {"leads": by_lead_status, "deals": by_deal_status}


analytics_service = AnalyticsService()
