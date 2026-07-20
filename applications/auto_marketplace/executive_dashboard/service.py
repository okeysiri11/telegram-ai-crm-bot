# Executive Dashboard — role-based dashboards.

from __future__ import annotations

from events.publisher import publish

from applications.auto_marketplace.analytics.engine import AnalyticsEngine, analytics_engine
from applications.auto_marketplace.business_intelligence.events import DashboardUpdatedEvent
from applications.auto_marketplace.business_intelligence.models import DashboardRole, DashboardSnapshot
from applications.auto_marketplace.kpi.service import KPIService, kpi_service
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ExecutiveDashboardService:
    _ROLE_TITLES = {
        DashboardRole.OWNER: "Owner Dashboard",
        DashboardRole.ADMINISTRATOR: "Administrator Dashboard",
        DashboardRole.SALES_MANAGER: "Sales Dashboard",
        DashboardRole.DEALER: "Dealer Dashboard",
        DashboardRole.FINANCE_MANAGER: "Finance Dashboard",
        DashboardRole.OPERATIONS: "Operations Dashboard",
        DashboardRole.AI_AGENT: "AI Dashboard",
    }

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        kpi: KPIService | None = None,
        analytics: AnalyticsEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._kpi = kpi or kpi_service
        self._analytics = analytics or analytics_engine

    async def get_dashboard(self, role: DashboardRole | str) -> DashboardSnapshot:
        if isinstance(role, str):
            role = DashboardRole(role)
        kpis = self._kpi.compute_all()
        widgets: list[dict] = []

        if role in {DashboardRole.OWNER, DashboardRole.ADMINISTRATOR}:
            widgets = [
                {"type": "kpi_grid", "data": [k.to_dict() for k in kpis]},
                {"type": "sales_chart", "data": self._analytics.sales_analytics()},
                {"type": "financial_chart", "data": self._analytics.financial_analytics()},
            ]
        elif role == DashboardRole.SALES_MANAGER:
            widgets = [
                {"type": "pipeline", "data": self._analytics.sales_analytics()},
                {"type": "kpis", "data": [k.to_dict() for k in kpis if k.name in {"lead_conversion", "average_deal_size", "vehicle_sales"}]},
            ]
        elif role == DashboardRole.FINANCE_MANAGER:
            widgets = [{"type": "financial", "data": self._analytics.financial_analytics()}]
            kpis = [k for k in kpis if k.name in {"revenue", "profit", "gross_margin"}]
        elif role == DashboardRole.DEALER:
            widgets = [{"type": "dealer", "data": self._analytics.dealer_analytics()}]
            kpis = [k for k in kpis if k.name in {"dealer_performance", "vehicle_sales"}]
        elif role == DashboardRole.OPERATIONS:
            widgets = [
                {"type": "inventory", "data": self._analytics.inventory_analytics()},
                {"type": "workflow", "data": self._analytics.workflow_analytics()},
            ]
        elif role == DashboardRole.AI_AGENT:
            widgets = [
                {"type": "agent", "data": self._analytics.agent_analytics()},
                {"type": "ai_accuracy", "data": {"ai_recommendation_accuracy": next((k.value for k in kpis if k.name == "ai_recommendation_accuracy"), 0)}},
            ]

        snapshot = DashboardSnapshot(
            role=role,
            title=self._ROLE_TITLES.get(role, "Dashboard"),
            widgets=widgets,
            kpis=kpis,
        )
        self._store.bi_dashboards.save(snapshot.snapshot_id, snapshot)
        await publish(DashboardUpdatedEvent(snapshot_id=snapshot.snapshot_id, role=role.value))
        return snapshot


executive_dashboard_service = ExecutiveDashboardService()
