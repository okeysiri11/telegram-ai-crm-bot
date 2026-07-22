"""Buyer profile management — Sprint 13.4."""

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


class BuyerProfile:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create(
        self,
        *,
        name: str,
        budget_max: float = 25000.0,
        budget_min: float = 0.0,
        preferred_brands: list[str] | None = None,
        preferred_models: list[str] | None = None,
        fuel: list[str] | None = None,
        ev_preference: bool = False,
        body_styles: list[str] | None = None,
        transmission: list[str] | None = None,
        regions: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("buyer name required")
        bid = _id("bai_buyer")
        profile = {
            "buyer_id": bid,
            "name": name,
            "budget": {"min": float(budget_min), "max": float(budget_max)},
            "preferred_brands": preferred_brands or [],
            "preferred_models": preferred_models or [],
            "fuel_preferences": fuel or (["electric"] if ev_preference else ["gasoline"]),
            "ev_preference": bool(ev_preference),
            "body_style_preferences": body_styles or [],
            "transmission_preferences": transmission or [],
            "region_preferences": regions or [],
            "purchase_history": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self.store.ba_profiles.save(bid, profile)

    def get(self, buyer_id: str) -> dict[str, Any]:
        item = self.store.ba_profiles.get(buyer_id)
        if item is None:
            raise NotFoundError("buyer", buyer_id)
        return item

    def update_budget(self, buyer_id: str, *, budget_min: float | None = None, budget_max: float | None = None) -> dict[str, Any]:
        profile = self.get(buyer_id)
        if budget_min is not None:
            profile["budget"]["min"] = float(budget_min)
        if budget_max is not None:
            profile["budget"]["max"] = float(budget_max)
        profile["updated_at"] = _now()
        return self.store.ba_profiles.save(buyer_id, profile)

    def add_purchase(self, buyer_id: str, *, vin: str, price: float, dealer: str = "") -> dict[str, Any]:
        profile = self.get(buyer_id)
        entry = {"vin": vin, "price": float(price), "dealer": dealer, "at": _now()}
        profile.setdefault("purchase_history", []).append(entry)
        profile["updated_at"] = _now()
        self.store.ba_profiles.save(buyer_id, profile)
        return entry

    def status(self) -> dict[str, Any]:
        return {"profiles": self.store.ba_profiles.count()}
