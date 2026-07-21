# OfferService — sales offer helpers for trading module.

from __future__ import annotations

from applications.agro_marketplace.marketplace.engine import MarketplaceEngine, marketplace_engine
from applications.agro_marketplace.marketplace.models import SalesOffer


class OfferService:
    def __init__(self, marketplace: MarketplaceEngine | None = None) -> None:
        self._marketplace = marketplace or marketplace_engine

    async def publish(self, offer: SalesOffer) -> SalesOffer:
        return await self._marketplace.publish_offer(offer)

    def list_offers(self):
        return self._marketplace.list_offers()

    def get(self, offer_id: str) -> SalesOffer:
        return self._marketplace.get_offer(offer_id)

    async def match(self, offer_id: str, request_id: str | None = None):
        return await self._marketplace.match_offer(offer_id, request_id)


offer_service = OfferService()
