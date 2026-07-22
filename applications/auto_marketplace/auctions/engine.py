# Auctions Engine — wholesale/auction lots and bids.

from __future__ import annotations

import time

from applications.auto_marketplace.marketplace.models import AuctionLot
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AuctionsEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create(self, lot: AuctionLot) -> AuctionLot:
        if not lot.listing_id:
            raise ValidationError("listing_id is required")
        if lot.current_bid <= 0:
            lot.current_bid = lot.start_price
        return self._store.auction_lots.save(lot.auction_id, lot)

    def get(self, auction_id: str) -> AuctionLot:
        lot = self._store.auction_lots.get(auction_id)
        if lot is None:
            raise NotFoundError("AuctionLot", auction_id)
        return lot

    def list_active(self) -> list[AuctionLot]:
        return [a for a in self._store.auction_lots.list_all() if a.active]

    def place_bid(self, auction_id: str, bidder_id: str, amount: float) -> AuctionLot:
        lot = self.get(auction_id)
        if not lot.active:
            raise ValidationError("auction is closed")
        if amount <= lot.current_bid:
            raise ValidationError("bid must exceed current bid")
        lot.current_bid = amount
        lot.bids.append({"bidder_id": bidder_id, "amount": amount, "at": time.time()})
        return self._store.auction_lots.save(auction_id, lot)

    def close(self, auction_id: str) -> AuctionLot:
        lot = self.get(auction_id)
        lot.active = False
        return self._store.auction_lots.save(auction_id, lot)

    def metrics(self) -> dict:
        return {"auctions": self._store.auction_lots.count(), "active": len(self.list_active())}


auctions_engine = AuctionsEngine()
