# DealService — deal CRUD and win/loss tracking.

from __future__ import annotations

import time

from events.publisher import publish
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.events import DealLostEvent, DealOpenedEvent, DealUpdatedEvent, DealWonEvent
from applications.auto_marketplace.crm.models import CRMDeal, DealStage
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DealService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        ai: AISalesAssistant | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._ai = ai or ai_sales_assistant

    async def create(self, deal: CRMDeal) -> CRMDeal:
        deal.probability = await self._ai.predict_deal_probability(deal)
        saved = self._store.crm_deals.save(deal.deal_id, deal)
        await publish(DealOpenedEvent(deal_id=saved.deal_id, customer_id=saved.customer_id, amount=saved.amount))
        return saved

    def get(self, deal_id: str) -> CRMDeal:
        deal = self._store.crm_deals.get(deal_id)
        if deal is None:
            raise NotFoundError("CRMDeal", deal_id)
        return deal

    def list_deals(self, *, stage: DealStage | None = None, dealer_id: str | None = None) -> list[CRMDeal]:
        items = self._store.crm_deals.list_all()
        if stage:
            items = [d for d in items if d.stage == stage]
        if dealer_id:
            items = [d for d in items if d.dealer_id == dealer_id]
        return items

    async def update_stage(self, deal_id: str, stage: DealStage) -> CRMDeal:
        deal = self.get(deal_id)
        deal.stage = stage
        deal.probability = await self._ai.predict_deal_probability(deal)
        saved = self._store.crm_deals.save(deal_id, deal)
        await publish(DealUpdatedEvent(deal_id=deal_id, stage=stage.value, probability=saved.probability))
        return saved

    async def mark_won(self, deal_id: str, *, amount: float | None = None) -> CRMDeal:
        deal = self.get(deal_id)
        deal.stage = DealStage.CLOSED_WON
        deal.win = True
        deal.closed_at = time.time()
        if amount is not None:
            deal.amount = amount
        deal.probability = 1.0
        saved = self._store.crm_deals.save(deal_id, deal)
        await publish(DealWonEvent(deal_id=deal_id, amount=saved.amount, customer_id=saved.customer_id))
        return saved

    async def mark_lost(self, deal_id: str, *, reason: str = "") -> CRMDeal:
        deal = self.get(deal_id)
        deal.stage = DealStage.CLOSED_LOST
        deal.win = False
        deal.closed_at = time.time()
        deal.probability = 0.0
        saved = self._store.crm_deals.save(deal_id, deal)
        await publish(DealLostEvent(deal_id=deal_id, reason=reason))
        return saved


deal_service = DealService()
