# CRMService — leads, deals, and pipeline management.

from __future__ import annotations

from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import Deal, DealStatus, Lead, LeadStatus, Offer
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CRMService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_lead(self, lead: Lead) -> Lead:
        return self._store.leads.save(lead.lead_id, lead)

    def get_lead(self, lead_id: str) -> Lead:
        lead = self._store.leads.get(lead_id)
        if lead is None:
            raise NotFoundError("Lead", lead_id)
        return lead

    def list_leads(self, *, status: LeadStatus | None = None) -> list[Lead]:
        items = self._store.leads.list_all()
        if status:
            items = [l for l in items if l.status == status]
        return items

    def update_lead_status(self, lead_id: str, status: LeadStatus) -> Lead:
        lead = self.get_lead(lead_id)
        lead.status = status
        return self._store.leads.save(lead_id, lead)

    def create_deal(self, deal: Deal) -> Deal:
        return self._store.deals.save(deal.deal_id, deal)

    def get_deal(self, deal_id: str) -> Deal:
        deal = self._store.deals.get(deal_id)
        if deal is None:
            raise NotFoundError("Deal", deal_id)
        return deal

    def add_offer(self, deal_id: str, offer: Offer) -> Deal:
        deal = self.get_deal(deal_id)
        offer.deal_id = deal_id
        deal.offers.append(offer)
        deal.status = DealStatus.NEGOTIATING
        return self._store.deals.save(deal_id, deal)

    def close_deal(self, deal_id: str, final_price: float) -> Deal:
        deal = self.get_deal(deal_id)
        deal.final_price = final_price
        deal.status = DealStatus.CLOSED
        return self._store.deals.save(deal_id, deal)


crm_service = CRMService()
