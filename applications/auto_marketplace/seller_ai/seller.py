"""Seller AI — listings, pricing guidance, demand — Sprint 13.5."""

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


class SellerAI:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create_seller(self, *, name: str, seller_type: str = "private", region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("seller name required")
        if seller_type not in ("private", "dealership", "auction_house", "exporter"):
            raise ValidationError("invalid seller_type")
        sid = _id("sai_seller")
        seller = {
            "seller_id": sid,
            "name": name,
            "seller_type": seller_type,
            "region": region,
            "created_at": _now(),
        }
        return self.store.sa_sellers.save(sid, seller)

    def create_listing(
        self,
        *,
        seller_id: str,
        vin: str,
        make: str,
        model: str,
        year: int | None = None,
        ask_price: float = 0.0,
        photos: list[str] | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        if self.store.sa_sellers.get(seller_id) is None:
            raise NotFoundError("seller", seller_id)
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required")
        lid = _id("sai_list")
        listing = {
            "listing_id": lid,
            "seller_id": seller_id,
            "vin": vin,
            "make": make,
            "model": model,
            "year": year,
            "ask_price": float(ask_price),
            "photos": photos or [],
            "description": description,
            "status": "draft",
            "created_at": _now(),
        }
        return self.store.sa_listings.save(lid, listing)

    def generate_listing_copy(self, listing_id: str) -> dict[str, Any]:
        listing = self.store.sa_listings.get(listing_id)
        if listing is None:
            raise NotFoundError("listing", listing_id)
        title = f"{listing.get('year') or ''} {listing.get('make')} {listing.get('model')}".strip()
        description = (
            f"{title} with VIN {listing['vin']}. "
            f"Priced at {listing.get('ask_price')} USD. Clean presentation ready for marketplace."
        )
        photo_quality = 0.9 if len(listing.get("photos") or []) >= 3 else 0.55
        rid = _id("sai_copy")
        result = {
            "copy_id": rid,
            "listing_id": listing_id,
            "title": title,
            "description": description,
            "photo_quality": photo_quality,
            "photo_quality_analysis": {
                "count": len(listing.get("photos") or []),
                "recommendation": "add_more_angles" if photo_quality < 0.7 else "good_coverage",
            },
            "generated_at": _now(),
        }
        listing["description"] = description
        listing["status"] = "ready"
        listing["updated_at"] = _now()
        self.store.sa_listings.save(listing_id, listing)
        return self.store.sa_listing_copy.save(rid, result)

    def analyze_market_position(
        self,
        *,
        listing_id: str,
        market_avg: float = 18000.0,
        demand_index: float = 0.6,
    ) -> dict[str, Any]:
        listing = self.store.sa_listings.get(listing_id)
        if listing is None:
            raise NotFoundError("listing", listing_id)
        ask = float(listing.get("ask_price") or 0)
        position = "above_market" if ask > market_avg * 1.05 else "below_market" if ask < market_avg * 0.95 else "at_market"
        sale_prob = max(0.05, min(0.95, demand_index * (1.1 if position != "above_market" else 0.75)))
        recommended = round(market_avg * (0.98 if demand_index < 0.5 else 1.02), 2)
        rid = _id("sai_pos")
        result = {
            "analysis_id": rid,
            "listing_id": listing_id,
            "market_avg": market_avg,
            "ask_price": ask,
            "market_position": position,
            "price_recommendation": recommended,
            "demand_prediction": round(demand_index, 2),
            "sale_probability": round(sale_prob, 2),
            "at": _now(),
        }
        return self.store.sa_market_analyses.save(rid, result)

    def seller_dashboard(self, seller_id: str) -> dict[str, Any]:
        listings = [l for l in self.store.sa_listings.list_all() if l.get("seller_id") == seller_id]
        return {
            "seller_id": seller_id,
            "listings": len(listings),
            "ready": len([l for l in listings if l.get("status") == "ready"]),
            "draft": len([l for l in listings if l.get("status") == "draft"]),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "sellers": self.store.sa_sellers.count(),
            "listings": self.store.sa_listings.count(),
            "analyses": self.store.sa_market_analyses.count(),
        }
