"""Deal negotiation AI — Sprint 13.4."""

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


class NegotiationAI:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def start(
        self,
        *,
        buyer_id: str,
        listing_id: str,
        list_price: float | None = None,
    ) -> dict[str, Any]:
        listing = self.store.ba_listings.get(listing_id)
        if listing is None and list_price is None:
            raise NotFoundError("listing", listing_id)
        price = float(list_price if list_price is not None else listing.get("price") or 0)
        nid = _id("bai_neg")
        session = {
            "negotiation_id": nid,
            "buyer_id": buyer_id,
            "listing_id": listing_id,
            "list_price": price,
            "offers": [],
            "seller_behavior": {"flexibility": 0.55, "urgency": 0.4},
            "status": "open",
            "started_at": _now(),
        }
        return self.store.ba_negotiations.save(nid, session)

    def generate_offer(self, negotiation_id: str, *, strategy: str = "fair") -> dict[str, Any]:
        session = self.store.ba_negotiations.get(negotiation_id)
        if session is None:
            raise NotFoundError("negotiation", negotiation_id)
        price = float(session["list_price"])
        mult = {"aggressive": 0.88, "fair": 0.93, "soft": 0.97}.get(strategy, 0.93)
        amount = round(price * mult, 2)
        offer = {"offer_id": _id("bai_off"), "side": "buyer", "amount": amount, "strategy": strategy, "at": _now()}
        session["offers"].append(offer)
        session["updated_at"] = _now()
        self.store.ba_negotiations.save(negotiation_id, session)
        return offer

    def generate_counter(self, negotiation_id: str, *, seller_offer: float | None = None) -> dict[str, Any]:
        session = self.store.ba_negotiations.get(negotiation_id)
        if session is None:
            raise NotFoundError("negotiation", negotiation_id)
        last_buyer = next((o for o in reversed(session["offers"]) if o.get("side") == "buyer"), None)
        buyer_amt = float(last_buyer["amount"]) if last_buyer else float(session["list_price"]) * 0.93
        seller_amt = float(seller_offer if seller_offer is not None else session["list_price"] * 0.98)
        mid = round((buyer_amt + seller_amt) / 2, 2)
        counter = {"offer_id": _id("bai_ctr"), "side": "buyer_counter", "amount": mid, "at": _now()}
        session["offers"].append(counter)
        flex = min(0.95, float(session["seller_behavior"]["flexibility"]) + 0.05)
        session["seller_behavior"]["flexibility"] = flex
        session["updated_at"] = _now()
        self.store.ba_negotiations.save(negotiation_id, session)
        return counter

    def strategy(self, negotiation_id: str) -> dict[str, Any]:
        session = self.store.ba_negotiations.get(negotiation_id)
        if session is None:
            raise NotFoundError("negotiation", negotiation_id)
        price = float(session["list_price"])
        discount = round(price * float(session["seller_behavior"]["flexibility"]) * 0.08, 2)
        return {
            "negotiation_id": negotiation_id,
            "price_strategy": {
                "walk_away": round(price * 0.90, 2),
                "target": round(price * 0.94, 2),
                "stretch": round(price * 0.97, 2),
            },
            "purchase_timing": "within_14_days" if session["seller_behavior"]["urgency"] > 0.5 else "within_30_days",
            "dealer_discount_prediction": discount,
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {"negotiations": self.store.ba_negotiations.count()}
