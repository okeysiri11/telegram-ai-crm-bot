"""AI vehicle search — Sprint 13.4."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class VehicleSearch:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def index_listing(
        self,
        *,
        vin: str,
        make: str,
        model: str,
        year: int | None = None,
        price: float = 0.0,
        dealer: str = "",
        fuel: str = "gasoline",
        body_style: str = "sedan",
        region: str = "",
        available: bool = True,
    ) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required")
        lid = _id("bai_list")
        listing = {
            "listing_id": lid,
            "vin": vin,
            "make": make,
            "model": model,
            "year": year,
            "price": float(price),
            "dealer": dealer,
            "fuel": fuel,
            "body_style": body_style,
            "region": region,
            "available": bool(available),
            "indexed_at": _now(),
        }
        return self.store.ba_listings.save(lid, listing)

    def natural_language_search(self, *, query: str, buyer_id: str = "") -> dict[str, Any]:
        q = (query or "").lower()
        if not q:
            raise ValidationError("query required")
        budget = None
        m = re.search(r"under\s+(\d[\d,]*)", q) or re.search(r"\$(\d[\d,]*)", q)
        if m:
            budget = float(m.group(1).replace(",", ""))
        listings = self.store.ba_listings.list_all()
        results = []
        for item in listings:
            blob = f"{item.get('make','')} {item.get('model','')} {item.get('fuel','')} {item.get('body_style','')}".lower()
            if any(tok in blob for tok in q.split() if len(tok) > 2):
                if budget is None or float(item.get("price") or 0) <= budget:
                    results.append(item)
        if buyer_id and self.store.ba_profiles.get(buyer_id):
            profile = self.store.ba_profiles.get(buyer_id)
            max_b = float(profile["budget"]["max"])
            results = [r for r in results if float(r.get("price") or 0) <= max_b]
        results.sort(key=lambda x: float(x.get("price") or 0))
        rid = _id("bai_search")
        payload = {
            "search_id": rid,
            "query": query,
            "buyer_id": buyer_id,
            "results": results[:20],
            "count": len(results),
            "at": _now(),
        }
        return self.store.ba_searches.save(rid, payload)

    def recommend(self, *, buyer_id: str, limit: int = 5) -> dict[str, Any]:
        profile = self.store.ba_profiles.get(buyer_id)
        if profile is None:
            raise NotFoundError("buyer", buyer_id)
        budget = float(profile["budget"]["max"])
        brands = {b.lower() for b in profile.get("preferred_brands") or []}
        fuels = {f.lower() for f in profile.get("fuel_preferences") or []}
        scored = []
        for item in self.store.ba_listings.list_all():
            if not item.get("available"):
                continue
            price = float(item.get("price") or 0)
            if price > budget:
                continue
            score = 50.0
            if (item.get("make") or "").lower() in brands:
                score += 25
            if (item.get("fuel") or "").lower() in fuels:
                score += 15
            if profile.get("ev_preference") and item.get("fuel") == "electric":
                score += 10
            scored.append((score, item))
        scored.sort(key=lambda x: (-x[0], float(x[1].get("price") or 0)))
        top = [s[1] for s in scored[:limit]]
        alts = [s[1] for s in scored[limit : limit + 3]]
        rid = _id("bai_rec")
        result = {
            "recommendation_id": rid,
            "buyer_id": buyer_id,
            "recommendations": top,
            "alternatives": alts,
            "at": _now(),
        }
        return self.store.ba_recommendations.save(rid, result)

    def compare(self, *, listing_ids: list[str]) -> dict[str, Any]:
        items = []
        for lid in listing_ids:
            item = self.store.ba_listings.get(lid)
            if item:
                items.append(item)
        if len(items) < 2:
            raise ValidationError("at least two listings required")
        rid = _id("bai_cmp")
        result = {
            "comparison_id": rid,
            "listings": items,
            "price_range": {
                "min": min(float(i.get("price") or 0) for i in items),
                "max": max(float(i.get("price") or 0) for i in items),
            },
            "dealers": sorted({i.get("dealer", "") for i in items if i.get("dealer")}),
            "at": _now(),
        }
        return self.store.ba_comparisons.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {
            "listings": self.store.ba_listings.count(),
            "searches": self.store.ba_searches.count(),
            "recommendations": self.store.ba_recommendations.count(),
        }
