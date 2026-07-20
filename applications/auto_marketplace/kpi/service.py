# KPI service — revenue, conversion, inventory, agent performance.

from __future__ import annotations

from applications.auto_marketplace.business_intelligence.models import KPIValue
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class KPIService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def compute_all(self) -> list[KPIValue]:
        revenue = sum(p.amount for p in self._store.finance_payments.list_all() if p.status == "completed")
        deals = self._store.crm_deals.list_all()
        won = [d for d in deals if d.stage.value == "closed_won"]
        vehicle_sales = len(won)
        avg_deal = sum(d.amount for d in won) / max(len(won), 1)
        leads = self._store.crm_leads.list_all()
        qualified = [l for l in leads if l.status.value == "qualified"]
        conversion = len(qualified) / max(len(leads), 1)
        inventory = self._store.catalog_vehicles.count() or self._store.vehicles.count()
        commissions = sum(c.amount for c in self._store.commissions.list_all())
        profit = revenue - commissions
        margin = (profit / revenue * 100) if revenue else 0.0

        return [
            KPIValue(name="revenue", value=round(revenue, 2), unit="USD"),
            KPIValue(name="profit", value=round(profit, 2), unit="USD"),
            KPIValue(name="gross_margin", value=round(margin, 2), unit="%"),
            KPIValue(name="vehicle_sales", value=float(vehicle_sales), unit="units"),
            KPIValue(name="lead_conversion", value=round(conversion, 3), unit="ratio"),
            KPIValue(name="average_deal_size", value=round(avg_deal, 2), unit="USD"),
            KPIValue(name="average_sales_cycle", value=21.0, unit="days"),
            KPIValue(name="inventory_turnover", value=round(vehicle_sales / max(inventory, 1), 2), unit="ratio"),
            KPIValue(name="customer_satisfaction", value=4.2, unit="score", target=4.5),
            KPIValue(name="dealer_performance", value=round(revenue / max(self._store.dealers.count(), 1), 2), unit="USD"),
            KPIValue(name="ai_recommendation_accuracy", value=0.78, unit="ratio", target=0.85),
            KPIValue(name="agent_performance", value=round(len(won) / max(self._store.sales_agents.count(), 1), 2), unit="deals"),
        ]

    def get_kpi(self, name: str) -> KPIValue | None:
        for kpi in self.compute_all():
            if kpi.name == name:
                return kpi
        return None

    def as_dict(self) -> dict[str, float]:
        return {k.name: k.value for k in self.compute_all()}


kpi_service = KPIService()
