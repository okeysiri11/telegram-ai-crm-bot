# Digital vehicle exchange between partners.

from __future__ import annotations

from applications.auto_marketplace.enterprise.models import ExchangeOffer
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DigitalExchangeEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_offer(self, offer: ExchangeOffer) -> ExchangeOffer:
        if not offer.vehicle_id or not offer.from_partner_id:
            raise ValidationError("vehicle_id and from_partner_id are required")
        offer.status = "open"
        return self._store.exchange_offers.save(offer.offer_id, offer)

    def accept(self, offer_id: str) -> ExchangeOffer:
        offer = self._store.exchange_offers.get(offer_id)
        if offer is None:
            raise NotFoundError("ExchangeOffer", offer_id)
        offer.status = "accepted"
        return self._store.exchange_offers.save(offer_id, offer)

    def list_offers(self, *, status: str = "") -> list[ExchangeOffer]:
        items = self._store.exchange_offers.list_all()
        if status:
            items = [o for o in items if o.status == status]
        return items

    def metrics(self) -> dict:
        return {"exchange_offers": self._store.exchange_offers.count()}


digital_exchange_engine = DigitalExchangeEngine()
