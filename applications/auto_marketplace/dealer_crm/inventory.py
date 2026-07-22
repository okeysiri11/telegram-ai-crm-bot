"""Inventory Intelligence — Sprint 13.3."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

STOCK_STATUSES = ["available", "reserved", "incoming", "sold"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class InventoryIntelligence:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def add_vehicle(
        self,
        *,
        vin: str,
        make: str = "",
        model: str = "",
        year: int | None = None,
        price: float = 0.0,
        warehouse: str = "main",
        dealership_id: str = "",
        status: str = "available",
    ) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required")
        if status not in STOCK_STATUSES:
            raise ValidationError(f"status must be one of {STOCK_STATUSES}")
        iid = _id("dcrm_inv")
        item = {
            "inventory_id": iid,
            "vin": vin,
            "make": make,
            "model": model,
            "year": year,
            "price": float(price),
            "warehouse": warehouse,
            "dealership_id": dealership_id,
            "status": status,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.dc_warehouses.save(
            warehouse,
            {"warehouse_id": warehouse, "name": warehouse, "updated_at": _now()},
        )
        return self.store.dc_inventory.save(iid, item)

    def update_status(self, inventory_id: str, *, status: str) -> dict[str, Any]:
        item = self.store.dc_inventory.get(inventory_id)
        if item is None:
            raise NotFoundError("inventory", inventory_id)
        if status not in STOCK_STATUSES:
            raise ValidationError(f"status must be one of {STOCK_STATUSES}")
        item["status"] = status
        item["updated_at"] = _now()
        return self.store.dc_inventory.save(inventory_id, item)

    def search_vin(self, vin: str) -> list[dict[str, Any]]:
        vin = (vin or "").strip().upper()
        return [i for i in self.store.dc_inventory.list_all() if i.get("vin") == vin]

    def list_by_status(self, status: str | None = None) -> list[dict[str, Any]]:
        items = self.store.dc_inventory.list_all()
        if status:
            return [i for i in items if i.get("status") == status]
        return items

    def optimize(self, *, dealership_id: str = "") -> dict[str, Any]:
        items = self.store.dc_inventory.list_all()
        if dealership_id:
            items = [i for i in items if i.get("dealership_id") == dealership_id]
        available = [i for i in items if i.get("status") == "available"]
        reserved = [i for i in items if i.get("status") == "reserved"]
        suggestions = []
        if len(available) > 8:
            suggestions.append("promote_aging_stock")
        if len(reserved) / max(1, len(items)) > 0.4:
            suggestions.append("review_reservations")
        if not available:
            suggestions.append("accelerate_incoming")
        rid = _id("dcrm_opt")
        result = {
            "optimization_id": rid,
            "dealership_id": dealership_id,
            "available": len(available),
            "reserved": len(reserved),
            "sold": len([i for i in items if i.get("status") == "sold"]),
            "incoming": len([i for i in items if i.get("status") == "incoming"]),
            "suggestions": suggestions or ["balanced"],
            "at": _now(),
        }
        return self.store.dc_optimizations.save(rid, result)

    def recommend(self, *, budget: float, make: str = "") -> dict[str, Any]:
        candidates = [
            i
            for i in self.store.dc_inventory.list_all()
            if i.get("status") == "available" and float(i.get("price") or 0) <= float(budget)
        ]
        if make:
            candidates = [c for c in candidates if (c.get("make") or "").lower() == make.lower()]
        candidates.sort(key=lambda x: float(x.get("price") or 0), reverse=True)
        top = candidates[:5]
        rid = _id("dcrm_rec")
        result = {
            "recommendation_id": rid,
            "budget": budget,
            "make": make,
            "vehicle_ids": [c["inventory_id"] for c in top],
            "vins": [c["vin"] for c in top],
            "at": _now(),
        }
        return self.store.dc_recommendations.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {
            "inventory": self.store.dc_inventory.count(),
            "warehouses": self.store.dc_warehouses.count(),
            "by_status": {s: len(self.list_by_status(s)) for s in STOCK_STATUSES},
        }
