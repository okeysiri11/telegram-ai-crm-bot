"""Sales Platform — Sprint 13.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

ACTIONS = ["buy", "sell", "auction", "reservation", "negotiation", "contract", "payment", "delivery"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SalesPlatform:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.actions = list(ACTIONS)

    def create(
        self,
        *,
        action: str,
        vehicle_id: str,
        customer_id: str = "",
        dealer_id: str = "",
        amount: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if action not in self.actions:
            raise ValidationError(f"action must be one of {self.actions}")
        if self.store.ea_vehicles.get(vehicle_id) is None:
            raise NotFoundError("vehicle", vehicle_id)
        sid = _id("easale")
        record = {
            "sale_id": sid,
            "action": action,
            "vehicle_id": vehicle_id,
            "customer_id": customer_id,
            "dealer_id": dealer_id,
            "amount": float(amount),
            "metadata": metadata or {},
            "status": "open" if action in ("auction", "negotiation", "reservation") else "completed",
            "created_at": _now(),
        }
        if action in ("buy", "sell"):
            inv = self.store.ea_inventory.get(vehicle_id)
            if inv:
                inv["status"] = "sold"
                inv["updated_at"] = _now()
                self.store.ea_inventory.save(vehicle_id, inv)
        return self.store.ea_sales.save(sid, record)

    def place_bid(self, *, auction_id: str, bidder_id: str, amount: float) -> dict[str, Any]:
        auction = self.store.ea_auctions.get(auction_id)
        if auction is None:
            raise NotFoundError("auction", auction_id)
        if auction.get("status") != "open":
            raise ValidationError("auction is not open")
        bid = {"bidder_id": bidder_id, "amount": float(amount), "at": _now()}
        auction.setdefault("bids", []).append(bid)
        auction["updated_at"] = _now()
        self.store.ea_auctions.save(auction_id, auction)
        return {"auction_id": auction_id, "bid": bid, "bids": len(auction["bids"])}

    def list_sales(self, action: str | None = None) -> list[dict[str, Any]]:
        items = self.store.ea_sales.list_all()
        if action:
            return [s for s in items if s.get("action") == action]
        return items

    def status(self) -> dict[str, Any]:
        return {"sales": self.store.ea_sales.count(), "actions": self.actions}
