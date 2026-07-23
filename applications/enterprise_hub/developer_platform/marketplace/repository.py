from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



class MarketplaceRepository:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def publish_listing(
        self,
        *,
        package_id: str,
        name: str,
        version: str = "1.0.0",
        author: str = "bidex",
        description: str = "",
        tags: list[str] | None = None,
        rating: float = 5.0,
    ) -> dict[str, Any]:
        if not package_id or not name:
            raise ValidationError("package_id and name are required")
        lid = _id("sdp_list")
        record = {
            "listing_id": lid,
            "package_id": package_id,
            "name": name,
            "version": version,
            "author": author,
            "description": description or name,
            "tags": list(tags or []),
            "rating": float(rating),
            "reviews": [],
            "downloads": 0,
            "published_at": _now(),
        }
        return self.store.sdp_listings.save(lid, record)

    def search(self, *, query: str = "", tag: str | None = None) -> list[dict[str, Any]]:
        items = self.store.sdp_listings.list_all()
        q = query.lower().strip()
        out = []
        for i in items:
            if q and q not in i.get("name", "").lower() and q not in i.get("description", "").lower():
                continue
            if tag and tag not in (i.get("tags") or []):
                continue
            out.append(i)
        return out

    def add_review(self, *, listing_id: str, author: str, rating: float, comment: str = "") -> dict[str, Any]:
        listing = self.store.sdp_listings.get(listing_id)
        if not listing:
            raise NotFoundError(f"listing not found: {listing_id}")
        review = {"author": author, "rating": float(rating), "comment": comment, "at": _now()}
        listing.setdefault("reviews", []).append(review)
        ratings = [r["rating"] for r in listing["reviews"]]
        listing["rating"] = sum(ratings) / len(ratings)
        return self.store.sdp_listings.save(listing_id, listing)

    def status(self) -> dict[str, Any]:
        items = self.store.sdp_listings.list_all()
        return {"listings": len(items), "avg_rating": (sum(i.get("rating", 0) for i in items) / len(items)) if items else 0}
