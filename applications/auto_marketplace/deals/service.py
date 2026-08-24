# DealService — deal CRUD and win/loss tracking.

from __future__ import annotations

import time

from events.publisher import publish
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.events import DealLostEvent, DealOpenedEvent, DealUpdatedEvent, DealWonEvent
from applications.auto_marketplace.crm.models import CRMDeal, DealStage
from applications.auto_marketplace.crm.persistence import CRMPersistence, get_crm_persistence
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DealService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        ai: AISalesAssistant | None = None,
        persistence: CRMPersistence | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._ai = ai or ai_sales_assistant
        self._persistence = persistence

    def _records(self) -> CRMPersistence:
        return self._persistence or get_crm_persistence()

    async def create(self, deal: CRMDeal) -> CRMDeal:
        deal.probability = await self._ai.predict_deal_probability(deal)
        saved = await self._records().save_deal(deal)
        await publish(DealOpenedEvent(deal_id=saved.deal_id, customer_id=saved.customer_id, amount=saved.amount))
        return saved

    async def get(self, deal_id: str) -> CRMDeal:
        deal = await self._records().get_deal(deal_id)
        if deal is None:
            raise NotFoundError("CRMDeal", deal_id)
        return deal

    async def list_deals(self, *, stage: DealStage | None = None, dealer_id: str | None = None) -> list[CRMDeal]:
        items = await self._records().list_deals()
        if stage:
            items = [d for d in items if d.stage == stage]
        if dealer_id:
            items = [d for d in items if d.dealer_id == dealer_id]
        return items

    async def update_stage(self, deal_id: str, stage: DealStage) -> CRMDeal:
        deal = await self.get(deal_id)
        deal.stage = stage
        deal.probability = await self._ai.predict_deal_probability(deal)
        saved = await self._records().save_deal(deal)
        await publish(DealUpdatedEvent(deal_id=deal_id, stage=stage.value, probability=saved.probability))
        return saved

    async def update(self, deal_id: str, **updates: object) -> CRMDeal:
        deal = await self.get(deal_id)
        for key, value in updates.items():
            if hasattr(deal, key) and value is not None:
                setattr(deal, key, value)
        deal.probability = await self._ai.predict_deal_probability(deal)
        saved = await self._records().save_deal(deal)
        await publish(
            DealUpdatedEvent(deal_id=deal_id, stage=saved.stage.value, probability=saved.probability)
        )
        return saved

    async def delete(self, deal_id: str) -> bool:
        await self.get(deal_id)
        return await self._records().delete_deal(deal_id)

    async def mark_won(self, deal_id: str, *, amount: float | None = None) -> CRMDeal:
        deal = await self.get(deal_id)
        deal.stage = DealStage.CLOSED_WON
        deal.win = True
        deal.closed_at = time.time()
        if amount is not None:
            deal.amount = amount
        deal.probability = 1.0
        saved = await self._records().save_deal(deal)
        await publish(DealWonEvent(deal_id=deal_id, amount=saved.amount, customer_id=saved.customer_id))
        return saved

    async def mark_lost(self, deal_id: str, *, reason: str = "") -> CRMDeal:
        deal = await self.get(deal_id)
        deal.stage = DealStage.CLOSED_LOST
        deal.win = False
        deal.closed_at = time.time()
        deal.probability = 0.0
        saved = await self._records().save_deal(deal)
        await publish(DealLostEvent(deal_id=deal_id, reason=reason))
        return saved


deal_service = DealService()
