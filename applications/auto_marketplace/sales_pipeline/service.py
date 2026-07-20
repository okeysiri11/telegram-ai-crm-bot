# SalesPipelineEngine — stages, forecasting, conversion analytics.

from __future__ import annotations

import time
from typing import Any

from applications.auto_marketplace.crm.models import CRMDeal, CRMLead, CRMLeadStatus, DealStage, SalesOpportunity
from applications.auto_marketplace.deals.service import DealService, deal_service
from applications.auto_marketplace.leads.service import LeadService, lead_service
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

_STAGE_ORDER = [
    DealStage.PROSPECT,
    DealStage.QUALIFICATION,
    DealStage.PROPOSAL,
    DealStage.NEGOTIATION,
    DealStage.APPROVAL,
    DealStage.CLOSED_WON,
]


class SalesPipelineEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        leads: LeadService | None = None,
        deals: DealService | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._leads = leads or lead_service
        self._deals = deals or deal_service

    async def qualify_lead(self, lead_id: str, *, agent_id: str = "") -> CRMLead:
        return await self._leads.qualify(lead_id, agent_id=agent_id)

    async def convert_lead_to_opportunity(self, lead_id: str, *, amount: float = 0.0) -> SalesOpportunity:
        lead = self._leads.get(lead_id)
        opp = SalesOpportunity(
            lead_id=lead_id,
            customer_id=lead.customer_id,
            dealer_id=lead.dealer_id,
            vehicle_id=lead.vehicle_id,
            stage=DealStage.QUALIFICATION,
            amount=amount,
            probability=0.25,
        )
        return self._store.opportunities.save(opp.opportunity_id, opp)

    async def open_deal_from_opportunity(self, opportunity_id: str) -> CRMDeal:
        opp = self._store.opportunities.get(opportunity_id)
        if opp is None:
            from applications.auto_marketplace.shared.exceptions import NotFoundError

            raise NotFoundError("SalesOpportunity", opportunity_id)
        deal = CRMDeal(
            opportunity_id=opportunity_id,
            customer_id=opp.customer_id,
            dealer_id=opp.dealer_id,
            vehicle_id=opp.vehicle_id,
            stage=opp.stage,
            amount=opp.amount,
            probability=opp.probability,
        )
        return await self._deals.create(deal)

    async def advance_stage(self, deal_id: str) -> CRMDeal:
        deal = self._deals.get(deal_id)
        if deal.stage == DealStage.CLOSED_WON or deal.stage == DealStage.CLOSED_LOST:
            return deal
        idx = _STAGE_ORDER.index(deal.stage) if deal.stage in _STAGE_ORDER else 0
        next_stage = _STAGE_ORDER[min(idx + 1, len(_STAGE_ORDER) - 1)]
        return await self._deals.update_stage(deal_id, next_stage)

    async def set_stage(self, deal_id: str, stage: DealStage) -> CRMDeal:
        return await self._deals.update_stage(deal_id, stage)

    def pipeline_view(self, *, dealer_id: str | None = None) -> dict[str, Any]:
        deals = self._deals.list_deals(dealer_id=dealer_id)
        stages: dict[str, list[dict]] = {s.value: [] for s in _STAGE_ORDER}
        for deal in deals:
            stages.setdefault(deal.stage.value, []).append(deal.to_dict())
        return {"stages": stages, "total_deals": len(deals)}

    def conversion_analytics(self) -> dict[str, Any]:
        leads = self._store.crm_leads.list_all()
        deals = self._store.crm_deals.list_all()
        qualified = sum(1 for l in leads if l.status == CRMLeadStatus.QUALIFIED)
        converted = sum(1 for l in leads if l.status == CRMLeadStatus.CONVERTED)
        won = sum(1 for d in deals if d.stage == DealStage.CLOSED_WON)
        lost = sum(1 for d in deals if d.stage == DealStage.CLOSED_LOST)
        total_leads = len(leads) or 1
        return {
            "leads_total": len(leads),
            "qualified_rate": round(qualified / total_leads, 4),
            "conversion_rate": round(converted / total_leads, 4),
            "win_rate": round(won / max(won + lost, 1), 4),
            "deals_won": won,
            "deals_lost": lost,
        }

    def forecast(self, *, days: int = 30) -> dict[str, Any]:
        horizon = time.time() + days * 86400
        deals = self._deals.list_deals()
        weighted = sum(d.amount * d.probability for d in deals if d.stage not in {DealStage.CLOSED_WON, DealStage.CLOSED_LOST})
        pipeline = sum(d.amount for d in deals if d.stage not in {DealStage.CLOSED_WON, DealStage.CLOSED_LOST})
        return {
            "forecast_days": days,
            "weighted_pipeline": round(weighted, 2),
            "total_pipeline": round(pipeline, 2),
            "deal_count": len(deals),
            "horizon_ts": horizon,
        }


sales_pipeline_engine = SalesPipelineEngine()
