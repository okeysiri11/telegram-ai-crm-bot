"""Auction platform — Sprint 13.5."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AuctionPlatform:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create_auction(
        self,
        *,
        listing_id: str,
        mode: str = "timed",
        reserve_price: float = 0.0,
        start_price: float = 0.0,
    ) -> dict[str, Any]:
        if mode not in ("live", "timed"):
            raise ValidationError("mode must be live or timed")
        if self.store.sa_listings.get(listing_id) is None:
            raise NotFoundError("listing", listing_id)
        aid = _id("sai_auc")
        auction = {
            "auction_id": aid,
            "listing_id": listing_id,
            "mode": mode,
            "reserve_price": float(reserve_price),
            "start_price": float(start_price),
            "current_bid": float(start_price),
            "bids": [],
            "proxy_bids": {},
            "status": "open",
            "winner": None,
            "created_at": _now(),
        }
        return self.store.sa_auctions.save(aid, auction)

    def place_bid(
        self,
        *,
        auction_id: str,
        bidder_id: str,
        amount: float,
        proxy_max: float | None = None,
    ) -> dict[str, Any]:
        auction = self.store.sa_auctions.get(auction_id)
        if auction is None:
            raise NotFoundError("auction", auction_id)
        if auction.get("status") != "open":
            raise ValidationError("auction is not open")
        amount = float(amount)
        if amount <= float(auction.get("current_bid") or 0):
            raise ValidationError("bid must exceed current bid")
        bid = {"bid_id": _id("sai_bid"), "bidder_id": bidder_id, "amount": amount, "at": _now()}
        auction["bids"].append(bid)
        auction["current_bid"] = amount
        if proxy_max is not None:
            auction.setdefault("proxy_bids", {})[bidder_id] = float(proxy_max)
            # auto bump if proxy allows
            for other, pmax in list(auction["proxy_bids"].items()):
                if other != bidder_id and float(pmax) > auction["current_bid"]:
                    auto = {
                        "bid_id": _id("sai_bid"),
                        "bidder_id": other,
                        "amount": round(auction["current_bid"] + 50, 2),
                        "proxy": True,
                        "at": _now(),
                    }
                    if auto["amount"] <= float(pmax):
                        auction["bids"].append(auto)
                        auction["current_bid"] = auto["amount"]
        auction["updated_at"] = _now()
        self.store.sa_auctions.save(auction_id, auction)
        return {"auction_id": auction_id, "bid": bid, "current_bid": auction["current_bid"], "bids": len(auction["bids"])}

    def close_auction(self, auction_id: str) -> dict[str, Any]:
        auction = self.store.sa_auctions.get(auction_id)
        if auction is None:
            raise NotFoundError("auction", auction_id)
        reserve = float(auction.get("reserve_price") or 0)
        current = float(auction.get("current_bid") or 0)
        winner = None
        if auction["bids"] and current >= reserve:
            winner = auction["bids"][-1]
            auction["status"] = "sold"
        else:
            auction["status"] = "reserve_not_met" if auction["bids"] else "unsold"
        auction["winner"] = winner
        auction["closed_at"] = _now()
        self.store.sa_auctions.save(auction_id, auction)
        return {
            "auction_id": auction_id,
            "status": auction["status"],
            "winner": winner,
            "final_bid": current,
        }

    def analytics(self, auction_id: str) -> dict[str, Any]:
        auction = self.store.sa_auctions.get(auction_id)
        if auction is None:
            raise NotFoundError("auction", auction_id)
        return {
            "auction_id": auction_id,
            "mode": auction.get("mode"),
            "bid_count": len(auction.get("bids") or []),
            "current_bid": auction.get("current_bid"),
            "reserve_price": auction.get("reserve_price"),
            "status": auction.get("status"),
            "proxy_bidders": len(auction.get("proxy_bids") or {}),
        }

    def status(self) -> dict[str, Any]:
        return {"auctions": self.store.sa_auctions.count()}
