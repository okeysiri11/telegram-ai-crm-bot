# Commercial Auction Engine — English/Dutch/timed/reserve/buy-now/auto-bid.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.models import AdvancedAuction, AuctionStatus, AuctionType


class CommercialAuctionEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def types(self) -> list[str]:
        return [t.value for t in AuctionType]

    def create(self, auction: AdvancedAuction) -> AdvancedAuction:
        if not auction.listing_id and not auction.vehicle_id:
            raise ValidationError("listing_id or vehicle_id is required")
        if auction.current_price <= 0:
            auction.current_price = auction.start_price
        if auction.auction_type == AuctionType.DUTCH and auction.current_price <= 0:
            auction.current_price = auction.start_price
        return self._store.advanced_auctions.save(auction.auction_id, auction)

    def get(self, auction_id: str) -> AdvancedAuction:
        auction = self._store.advanced_auctions.get(auction_id)
        if auction is None:
            raise NotFoundError("AdvancedAuction", auction_id)
        return auction

    def list_auctions(self, *, status: str | None = None, auction_type: str | None = None) -> list[AdvancedAuction]:
        items = self._store.advanced_auctions.list_all()
        if status:
            items = [a for a in items if a.status.value == status]
        if auction_type:
            items = [a for a in items if a.auction_type.value == auction_type]
        return items

    def start(self, auction_id: str) -> AdvancedAuction:
        auction = self.get(auction_id)
        auction.status = AuctionStatus.LIVE
        if not auction.ends_at:
            auction.ends_at = time.time() + 86400
        return self._store.advanced_auctions.save(auction_id, auction)

    def place_bid(self, auction_id: str, bidder_id: str, amount: float) -> AdvancedAuction:
        auction = self.get(auction_id)
        if auction.status != AuctionStatus.LIVE:
            raise ValidationError("auction is not live")
        if auction.ends_at and time.time() > auction.ends_at:
            auction.status = AuctionStatus.EXPIRED
            self._store.advanced_auctions.save(auction_id, auction)
            raise ValidationError("auction expired")

        if auction.auction_type == AuctionType.DUTCH:
            # Dutch: bid accepts current price or lower step
            if amount > auction.current_price:
                raise ValidationError("dutch bid must be at or below current price")
            auction.current_price = amount
            auction.winner_id = bidder_id
            auction.status = AuctionStatus.SOLD
        else:
            if amount <= auction.current_price:
                raise ValidationError("bid must exceed current price")
            auction.current_price = amount
        auction.bid_history.append({"bidder_id": bidder_id, "amount": amount, "at": time.time()})
        self._apply_auto_bids(auction)
        return self._store.advanced_auctions.save(auction_id, auction)

    def register_auto_bid(self, auction_id: str, bidder_id: str, max_amount: float) -> AdvancedAuction:
        auction = self.get(auction_id)
        auction.auto_bids.append({"bidder_id": bidder_id, "max_amount": max_amount})
        self._apply_auto_bids(auction)
        return self._store.advanced_auctions.save(auction_id, auction)

    def _apply_auto_bids(self, auction: AdvancedAuction) -> None:
        if auction.auction_type == AuctionType.DUTCH or auction.status != AuctionStatus.LIVE:
            return
        changed = True
        while changed:
            changed = False
            for auto in sorted(auction.auto_bids, key=lambda a: -a["max_amount"]):
                if auto["max_amount"] > auction.current_price:
                    step = round(auction.current_price + max(50.0, auction.current_price * 0.01), 2)
                    if step <= auto["max_amount"]:
                        auction.current_price = step
                        auction.bid_history.append(
                            {"bidder_id": auto["bidder_id"], "amount": step, "at": time.time(), "auto": True}
                        )
                        changed = True

    def buy_now(self, auction_id: str, buyer_id: str) -> AdvancedAuction:
        auction = self.get(auction_id)
        if auction.buy_now_price is None:
            raise ValidationError("buy now is not enabled")
        if auction.status != AuctionStatus.LIVE:
            raise ValidationError("auction is not live")
        auction.current_price = auction.buy_now_price
        auction.winner_id = buyer_id
        auction.status = AuctionStatus.SOLD
        auction.bid_history.append({"bidder_id": buyer_id, "amount": auction.buy_now_price, "at": time.time(), "buy_now": True})
        return self._store.advanced_auctions.save(auction_id, auction)

    def close(self, auction_id: str) -> AdvancedAuction:
        auction = self.get(auction_id)
        if auction.reserve_price and auction.current_price < auction.reserve_price:
            auction.status = AuctionStatus.RESERVE_NOT_MET
        elif auction.bid_history:
            auction.status = AuctionStatus.SOLD
            if not auction.winner_id:
                auction.winner_id = auction.bid_history[-1]["bidder_id"]
        else:
            auction.status = AuctionStatus.EXPIRED
        return self._store.advanced_auctions.save(auction_id, auction)

    def metrics(self) -> dict:
        items = self._store.advanced_auctions.list_all()
        return {
            "auctions": len(items),
            "live": len([a for a in items if a.status == AuctionStatus.LIVE]),
            "types": self.types(),
        }


commercial_auction_engine = CommercialAuctionEngine()
