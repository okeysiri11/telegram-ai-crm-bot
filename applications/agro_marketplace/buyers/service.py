# BuyerService — buyer account management.

from __future__ import annotations

from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import Buyer
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class BuyerService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def list_buyers(self) -> list[Buyer]:
        return self._store.buyers.list_all()

    def get_buyer(self, buyer_id: str) -> Buyer:
        buyer = self._store.buyers.get(buyer_id)
        if buyer is None:
            raise NotFoundError("Buyer", buyer_id)
        return buyer

    def create_buyer(self, buyer: Buyer) -> Buyer:
        if not buyer.name or not buyer.email:
            raise ValidationError("name and email are required")
        return self._store.buyers.save(buyer.buyer_id, buyer)


buyer_service = BuyerService()
