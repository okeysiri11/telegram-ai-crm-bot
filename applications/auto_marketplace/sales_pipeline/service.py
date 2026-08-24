# SalesPipelineEngine — stages, forecasting, conversion analytics.

from __future__ import annotations

import time
from typing import Any

from applications.auto_marketplace.crm.models import CRMDeal, CRMLead, CRMLeadStatus, DealStage, SalesOpportunity
from applications.auto_marketplace.crm.persistence import CRMPersistence, get_crm_persistence
from applications.auto_marketplace.deals.service import DealService, deal_service
from applications.auto_marketplace.leads.service import LeadService, lead_service
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

_CONVERTED_DEAL_ID_KEY = "converted_deal_id"
_CONVERTED_CUSTOMER_ID_KEY = "converted_customer_id"

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
        persistence: CRMPersistence | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._leads = leads or lead_service
        self._deals = deals or deal_service
        self._persistence = persistence

    def _records(self) -> CRMPersistence:
        return self._persistence or get_crm_persistence()

    async def qualify_lead(self, lead_id: str, *, agent_id: str = "") -> CRMLead:
        return await self._leads.qualify(lead_id, agent_id=agent_id)

    def _customers(self):
        from applications.auto_marketplace.customers.profile_service import CustomerProfileService, customer_profile_service

        if self._persistence is not None:
            return CustomerProfileService(store=self._store, persistence=self._persistence)
        return customer_profile_service

    async def _ensure_conversion_customer(self, lead: CRMLead, *, agent_id: str) -> tuple[CRMLead, str]:
        from applications.auto_marketplace.crm.models import CustomerProfile

        customers = self._customers()
        meta = dict(lead.metadata)
        customer_id = str(lead.customer_id or meta.get(_CONVERTED_CUSTOMER_ID_KEY) or "")
        if customer_id:
            try:
                await customers.get(customer_id)
                if not lead.customer_id or _CONVERTED_CUSTOMER_ID_KEY not in meta:
                    meta[_CONVERTED_CUSTOMER_ID_KEY] = customer_id
                    lead = await self._leads.update(lead.lead_id, customer_id=customer_id, metadata=meta)
                return lead, customer_id
            except NotFoundError:
                customer_id = ""
        name = (lead.notes or "").strip() or f"Lead {lead.lead_id[:8]}"
        profile = CustomerProfile(
            first_name=name[:80],
            last_name="",
            owner_agent_id=agent_id or lead.assigned_agent_id,
            tags=["converted-from-lead"],
            preferences={"source_lead_id": lead.lead_id},
        )
        created = await customers.create(profile)
        meta[_CONVERTED_CUSTOMER_ID_KEY] = created.customer_id
        lead = await self._leads.update(lead.lead_id, customer_id=created.customer_id, metadata=meta)
        return lead, created.customer_id

    async def convert_lead_to_deal(self, lead_id: str, *, amount: float = 0.0, agent_id: str = "") -> CRMDeal:
        """Idempotent lead → durable customer + deal. Ids stored on lead.metadata."""
        from applications.auto_marketplace.activities.service import activity_service

        lead = await self._leads.get(lead_id)
        lead, customer_id = await self._ensure_conversion_customer(lead, agent_id=agent_id)
        existing_id = str(lead.metadata.get(_CONVERTED_DEAL_ID_KEY) or "")
        created: CRMDeal | None = None
        if existing_id:
            try:
                created = await self._deals.get(existing_id)
            except NotFoundError:
                created = None
        if created is None:
            deal = CRMDeal(
                customer_id=customer_id,
                dealer_id=lead.dealer_id,
                vehicle_id=lead.vehicle_id,
                amount=amount,
                owner_agent_id=agent_id or lead.assigned_agent_id,
                stage=DealStage.QUALIFICATION,
            )
            created = await self._deals.create(deal)
        meta = dict(lead.metadata)
        meta[_CONVERTED_DEAL_ID_KEY] = created.deal_id
        meta[_CONVERTED_CUSTOMER_ID_KEY] = customer_id
        if lead.status != CRMLeadStatus.CONVERTED or lead.customer_id != customer_id or lead.metadata.get(_CONVERTED_DEAL_ID_KEY) != created.deal_id:
            await self._leads.update(
                lead_id,
                status=CRMLeadStatus.CONVERTED,
                customer_id=customer_id,
                metadata=meta,
            )
        await activity_service.record_event(
            "lead_converted",
            subject="Lead converted",
            body=created.deal_id,
            customer_id=customer_id,
            lead_id=lead_id,
            deal_id=created.deal_id,
            agent_id=agent_id or lead.assigned_agent_id,
            idempotency_key=f"lead_converted:{lead_id}",
        )
        return created

    async def convert_lead_to_opportunity(self, lead_id: str, *, amount: float = 0.0) -> SalesOpportunity:
        lead = await self._leads.get(lead_id)
        deal = await self.convert_lead_to_deal(lead_id, amount=amount)
        if deal.opportunity_id:
            existing = self._store.opportunities.get(deal.opportunity_id)
            if existing is not None:
                return existing
        opp = SalesOpportunity(
            lead_id=lead_id,
            customer_id=lead.customer_id,
            dealer_id=lead.dealer_id,
            vehicle_id=lead.vehicle_id,
            stage=deal.stage,
            amount=amount or deal.amount,
            probability=deal.probability,
        )
        saved = self._store.opportunities.save(opp.opportunity_id, opp)
        if not deal.opportunity_id:
            await self._deals.update(deal.deal_id, opportunity_id=saved.opportunity_id)
        return saved

    async def open_deal_from_opportunity(self, opportunity_id: str) -> CRMDeal:
        for deal in await self._deals.list_deals():
            if deal.opportunity_id == opportunity_id:
                return deal
        opp = self._store.opportunities.get(opportunity_id)
        if opp is None:
            raise NotFoundError("SalesOpportunity", opportunity_id)
        if opp.lead_id:
            existing_id = ""
            try:
                lead = await self._leads.get(opp.lead_id)
                existing_id = str(lead.metadata.get(_CONVERTED_DEAL_ID_KEY) or "")
            except NotFoundError:
                existing_id = ""
            if existing_id:
                try:
                    return await self._deals.get(existing_id)
                except NotFoundError:
                    pass
        deal = CRMDeal(
            opportunity_id=opportunity_id,
            customer_id=opp.customer_id,
            dealer_id=opp.dealer_id,
            vehicle_id=opp.vehicle_id,
            stage=opp.stage,
            amount=opp.amount,
            probability=opp.probability,
        )
        created = await self._deals.create(deal)
        if opp.lead_id:
            try:
                lead = await self._leads.get(opp.lead_id)
                meta = dict(lead.metadata)
                meta[_CONVERTED_DEAL_ID_KEY] = created.deal_id
                await self._leads.update(opp.lead_id, status=CRMLeadStatus.CONVERTED, metadata=meta)
            except NotFoundError:
                pass
        return created

    async def advance_stage(self, deal_id: str) -> CRMDeal:
        deal = await self._deals.get(deal_id)
        if deal.stage == DealStage.CLOSED_WON or deal.stage == DealStage.CLOSED_LOST:
            return deal
        idx = _STAGE_ORDER.index(deal.stage) if deal.stage in _STAGE_ORDER else 0
        next_stage = _STAGE_ORDER[min(idx + 1, len(_STAGE_ORDER) - 1)]
        return await self._deals.update_stage(deal_id, next_stage)

    async def set_stage(self, deal_id: str, stage: DealStage) -> CRMDeal:
        return await self._deals.update_stage(deal_id, stage)

    async def pipeline_view(self, *, dealer_id: str | None = None) -> dict[str, Any]:
        deals = await self._deals.list_deals(dealer_id=dealer_id)
        stages: dict[str, list[dict]] = {s.value: [] for s in _STAGE_ORDER}
        for deal in deals:
            stages.setdefault(deal.stage.value, []).append(deal.to_dict())
        return {"stages": stages, "total_deals": len(deals)}

    async def conversion_analytics(self) -> dict[str, Any]:
        records = self._records()
        leads = await records.list_leads()
        deals = await records.list_deals()
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

    async def forecast(self, *, days: int = 30) -> dict[str, Any]:
        horizon = time.time() + days * 86400
        deals = await self._deals.list_deals()
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
