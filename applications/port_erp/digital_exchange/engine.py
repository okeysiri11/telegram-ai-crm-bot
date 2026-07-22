# Digital Exchange Engine — capacity/price offers across the partner network.

from __future__ import annotations

from applications.port_erp.enterprise.models import ExchangeOffer
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class DigitalExchangeEngine:
    """Publish and match capacity/price offers on the digital exchange."""

    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def publish(self, offer: ExchangeOffer) -> ExchangeOffer:
        if not offer.partner_id:
            raise ValidationError("partner_id is required")
        if offer.price < 0 or offer.capacity_teu < 0:
            raise ValidationError("price and capacity must be non-negative")
        return self._store.exchange_offers.save(offer.offer_id, offer)

    def get(self, offer_id: str) -> ExchangeOffer:
        offer = self._store.exchange_offers.get(offer_id)
        if offer is None:
            raise NotFoundError("exchange_offer", offer_id)
        return offer

    def list_offers(self, *, origin: str = "", destination: str = "") -> list[ExchangeOffer]:
        offers = self._store.exchange_offers.list_all()
        if origin:
            offers = [o for o in offers if o.origin.lower() == origin.lower()]
        if destination:
            offers = [o for o in offers if o.destination.lower() == destination.lower()]
        return offers

    def match(self, *, origin: str, destination: str, min_capacity: float = 0) -> list[ExchangeOffer]:
        offers = self.list_offers(origin=origin, destination=destination)
        matched = [o for o in offers if o.capacity_teu >= min_capacity]
        return sorted(matched, key=lambda o: o.price)


digital_exchange_engine = DigitalExchangeEngine()
