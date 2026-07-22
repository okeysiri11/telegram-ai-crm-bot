# Buyers Engine — Sprint 10.1 buyer profiles.

from __future__ import annotations

from applications.auto_marketplace.foundation.models import Buyer
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class BuyersEngine:
    """Buyer registration and lookup."""

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def register(self, buyer: Buyer) -> Buyer:
        if not buyer.email and not buyer.phone:
            raise ValidationError("buyer email or phone is required")
        return self._store.buyers.save(buyer.buyer_id, buyer)

    def get(self, buyer_id: str) -> Buyer:
        buyer = self._store.buyers.get(buyer_id)
        if buyer is None:
            raise NotFoundError("Buyer", buyer_id)
        return buyer

    def list_buyers(self, *, region: str = "") -> list[Buyer]:
        items = self._store.buyers.list_all()
        if region:
            items = [b for b in items if b.region.lower() == region.lower()]
        return items

    def metrics(self) -> dict:
        return {"buyers": self._store.buyers.count()}


buyers_engine = BuyersEngine()
