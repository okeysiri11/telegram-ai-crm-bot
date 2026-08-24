# Analytics Engine — sales, financial, customer, inventory, marketing, dealer, workflow, agent.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.crm.persistence import get_crm_persistence
from applications.auto_marketplace.kpi.service import KPIService, kpi_service
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AnalyticsEngine:
    def __init__(self, store: MarketplaceStore | None = None, kpi: KPIService | None = None) -> None:
        self._store = store or marketplace_store
        self._kpi = kpi or kpi_service

    async def sales_analytics(self) -> dict[str, Any]:
        records = get_crm_persistence()
        leads = await records.list_leads()
        deals = await records.list_deals()
        by_source: dict[str, int] = {}
        for lead in leads:
            by_source[lead.source.value] = by_source.get(lead.source.value, 0) + 1
        by_stage: dict[str, int] = {}
        for deal in deals:
            by_stage[deal.stage.value] = by_stage.get(deal.stage.value, 0) + 1
        return {"leads_by_source": by_source, "deals_by_stage": by_stage, "total_pipeline_value": sum(d.amount for d in deals)}

    def financial_analytics(self) -> dict[str, Any]:
        payments = self._store.finance_payments.list_all()
        invoices = self._store.finance_invoices.list_all()
        return {
            "total_revenue": sum(p.amount for p in payments if p.status == "completed"),
            "outstanding_invoices": len([i for i in invoices if i.status.value not in {"paid", "void"}]),
            "refunds": self._store.refunds.count(),
            "settlements": self._store.dealer_settlements.count(),
        }

    async def customer_analytics(self) -> dict[str, Any]:
        profiles = await get_crm_persistence().list_customers()
        segments: dict[str, int] = {}
        for p in profiles:
            segments[p.segment] = segments.get(p.segment, 0) + 1
        return {"total_customers": len(profiles), "by_segment": segments, "avg_intent_score": round(sum(p.intent_score for p in profiles) / max(len(profiles), 1), 2)}

    def inventory_analytics(self) -> dict[str, Any]:
        vehicles = self._store.catalog_vehicles.list_all() or self._store.vehicles.list_all()
        total_value = sum(getattr(v, "price", 0) or 0 for v in vehicles)
        return {"total_units": len(vehicles), "total_inventory_value": round(total_value, 2), "avg_price": round(total_value / max(len(vehicles), 1), 2)}

    async def marketing_analytics(self) -> dict[str, Any]:
        leads = await get_crm_persistence().list_leads()
        channels = {"web": 0, "mobile": 0, "referral": 0, "other": 0}
        for lead in leads:
            src = lead.source.value
            key = src if src in channels else "other"
            channels[key] = channels.get(key, 0) + 1
        return {"leads_by_channel": channels}

    async def dealer_analytics(self) -> dict[str, Any]:
        dealers = self._store.dealers.list_all()
        deals = await get_crm_persistence().list_deals()
        result: list[dict] = []
        for dealer in dealers:
            did = getattr(dealer, "dealer_id", "")
            dealer_deals = [d for d in deals if d.dealer_id == did]
            result.append({"dealer_id": did, "name": getattr(dealer, "name", ""), "deals": len(dealer_deals), "revenue": sum(d.amount for d in dealer_deals)})
        return {"dealers": result}

    async def workflow_analytics(self) -> dict[str, Any]:
        records = get_crm_persistence()
        return {
            "crm_tasks": await records.count_tasks(),
            "meetings": await records.count_meetings(),
            "reminders": await records.count_reminders(),
        }

    async def agent_analytics(self) -> dict[str, Any]:
        agents = self._store.sales_agents.list_all()
        leads = await get_crm_persistence().list_leads()
        return {
            "total_agents": len(agents),
            "ai_conversations": self._store.conversation_sessions.count(),
            "avg_lead_score": round(sum(l.score for l in leads) / max(len(leads), 1), 2),
        }

    async def all_analytics(self) -> dict[str, Any]:
        return {
            "sales": await self.sales_analytics(),
            "financial": self.financial_analytics(),
            "customer": await self.customer_analytics(),
            "inventory": self.inventory_analytics(),
            "marketing": await self.marketing_analytics(),
            "dealer": await self.dealer_analytics(),
            "workflow": await self.workflow_analytics(),
            "agent": await self.agent_analytics(),
        }


analytics_engine = AnalyticsEngine()
