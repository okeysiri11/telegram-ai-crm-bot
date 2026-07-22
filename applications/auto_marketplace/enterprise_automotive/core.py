"""Marketplace Core registries — Sprint 13.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

VEHICLE_TYPES = [
    "car",
    "motorcycle",
    "truck",
    "commercial",
    "special_equipment",
    "electric",
    "hybrid",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MarketplaceCore:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def register_vin(self, *, vin: str, make: str = "", model: str = "", year: int | None = None) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("VIN must be at least 11 characters")
        existing = self.store.ea_vins.get(vin)
        if existing:
            return existing
        entry = {"vin": vin, "make": make, "model": model, "year": year, "registered_at": _now()}
        return self.store.ea_vins.save(vin, entry)

    def register_vehicle(
        self,
        *,
        vin: str,
        vehicle_type: str = "car",
        make: str = "",
        model: str = "",
        year: int | None = None,
        price: float = 0.0,
        dealer_id: str = "",
    ) -> dict[str, Any]:
        if vehicle_type not in VEHICLE_TYPES:
            raise ValidationError(f"vehicle_type must be one of {VEHICLE_TYPES}")
        vin_rec = self.register_vin(vin=vin, make=make, model=model, year=year)
        vid = _id("eaveh")
        vehicle = {
            "vehicle_id": vid,
            "vin": vin_rec["vin"],
            "vehicle_type": vehicle_type,
            "make": make or vin_rec.get("make", ""),
            "model": model or vin_rec.get("model", ""),
            "year": year or vin_rec.get("year"),
            "price": float(price),
            "dealer_id": dealer_id,
            "status": "listed",
            "created_at": _now(),
        }
        self.store.ea_vehicles.save(vid, vehicle)
        self.store.ea_inventory.save(
            vid,
            {"inventory_id": vid, "vehicle_id": vid, "status": "in_stock", "updated_at": _now()},
        )
        return vehicle

    def register_dealer(self, *, name: str, region: str = "", contact: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("dealer name required")
        did = _id("eadealer")
        dealer = {
            "dealer_id": did,
            "name": name,
            "region": region,
            "contact": contact,
            "status": "active",
            "created_at": _now(),
        }
        return self.store.ea_dealers.save(did, dealer)

    def register_customer(self, *, name: str, email: str = "", phone: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("customer name required")
        cid = _id("eacust")
        customer = {
            "customer_id": cid,
            "name": name,
            "email": email,
            "phone": phone,
            "status": "active",
            "created_at": _now(),
        }
        return self.store.ea_customers.save(cid, customer)

    def create_auction(self, *, vehicle_id: str, reserve_price: float = 0.0) -> dict[str, Any]:
        if self.store.ea_vehicles.get(vehicle_id) is None:
            raise NotFoundError("vehicle", vehicle_id)
        aid = _id("eaauc")
        auction = {
            "auction_id": aid,
            "vehicle_id": vehicle_id,
            "reserve_price": float(reserve_price),
            "status": "open",
            "bids": [],
            "created_at": _now(),
        }
        return self.store.ea_auctions.save(aid, auction)

    def register_import(self, *, origin: str, vehicle_count: int = 1, notes: str = "") -> dict[str, Any]:
        iid = _id("eaimp")
        record = {
            "import_id": iid,
            "origin": origin,
            "vehicle_count": int(vehicle_count),
            "notes": notes,
            "status": "registered",
            "created_at": _now(),
        }
        return self.store.ea_imports.save(iid, record)

    def inventory_update(self, vehicle_id: str, *, status: str) -> dict[str, Any]:
        item = self.store.ea_inventory.get(vehicle_id)
        if item is None:
            raise NotFoundError("inventory", vehicle_id)
        item["status"] = status
        item["updated_at"] = _now()
        return self.store.ea_inventory.save(vehicle_id, item)

    def list_vehicles(self, vehicle_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.ea_vehicles.list_all()
        if vehicle_type:
            return [v for v in items if v.get("vehicle_type") == vehicle_type]
        return items

    def status(self) -> dict[str, Any]:
        return {
            "vehicles": self.store.ea_vehicles.count(),
            "vins": self.store.ea_vins.count(),
            "dealers": self.store.ea_dealers.count(),
            "customers": self.store.ea_customers.count(),
            "auctions": self.store.ea_auctions.count(),
            "imports": self.store.ea_imports.count(),
            "inventory": self.store.ea_inventory.count(),
            "vehicle_types": VEHICLE_TYPES,
        }
