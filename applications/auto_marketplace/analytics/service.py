# AnalyticsService — marketplace metrics and reporting.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.crm.metrics import crm_metrics
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AnalyticsService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def dashboard_metrics(self) -> dict[str, Any]:
        crm = crm_metrics.cached()
        return {
            "vehicles": self._store.vehicles.count(),
            "dealers": self._store.dealers.count(),
            "customers": crm.get("customers", 0),
            "leads": crm.get("leads", 0),
            "deals": crm.get("deals", 0),
            "tasks": crm.get("tasks", 0),
            "activities": crm.get("activities", 0),
            "calls": crm.get("calls", 0),
            "emails": crm.get("emails", 0),
            "meetings": crm.get("meetings", 0),
            "reminders": crm.get("reminders", 0),
            "opportunities": crm.get("opportunities", 0),
            "payments": self._store.payments.count(),
            "deliveries": self._store.deliveries.count(),
        }

    def sales_pipeline(self) -> dict[str, Any]:
        crm = crm_metrics.cached()
        return {
            "leads": dict(crm.get("leads_by_status") or {}),
            "deals": dict(crm.get("deals_by_stage") or {}),
        }

    async def dashboard_metrics_durable(self, tenant_id: str | None = None) -> dict[str, Any]:
        await crm_metrics.refresh(tenant_id)
        return self.dashboard_metrics()

    async def sales_pipeline_durable(self, tenant_id: str | None = None) -> dict[str, Any]:
        await crm_metrics.refresh(tenant_id)
        return self.sales_pipeline()


analytics_service = AnalyticsService()
