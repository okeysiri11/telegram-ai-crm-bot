"""Agro marketplace and farm registry."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AgroMarketplace:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.categories = list(DEFAULT_CONFIG.listing_categories)

    def register_supplier(self, *, name: str, region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("supplier name required")
        sid = _id("ae_sup")
        return self.store.suppliers.save(
            sid, {"supplier_id": sid, "name": name, "region": region, "created_at": _now()}
        )

    def register_buyer(self, *, name: str, region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("buyer name required")
        bid = _id("ae_buy")
        return self.store.buyers.save(
            bid, {"buyer_id": bid, "name": name, "region": region, "created_at": _now()}
        )

    def create_listing(
        self,
        *,
        category: str,
        side: str,
        title: str,
        quantity: float = 1.0,
        unit: str = "t",
        price: float = 0.0,
        party_id: str = "",
    ) -> dict[str, Any]:
        if category not in self.categories:
            raise ValidationError(f"category must be one of {self.categories}")
        if side not in ("buy", "sell"):
            raise ValidationError("side must be buy or sell")
        if not title:
            raise ValidationError("title required")
        lid = _id("ae_list")
        listing = {
            "listing_id": lid,
            "category": category,
            "side": side,
            "title": title,
            "quantity": float(quantity),
            "unit": unit,
            "price": float(price),
            "party_id": party_id,
            "status": "open",
            "created_at": _now(),
        }
        return self.store.listings.save(lid, listing)

    def place_order(self, *, listing_id: str, counterparty_id: str, quantity: float | None = None) -> dict[str, Any]:
        listing = self.store.listings.get(listing_id)
        if listing is None:
            raise NotFoundError("listing", listing_id)
        oid = _id("ae_ord")
        order = {
            "order_id": oid,
            "listing_id": listing_id,
            "category": listing["category"],
            "side": listing["side"],
            "counterparty_id": counterparty_id,
            "quantity": float(quantity if quantity is not None else listing["quantity"]),
            "price": listing["price"],
            "status": "confirmed",
            "created_at": _now(),
        }
        listing["status"] = "matched"
        self.store.listings.save(listing_id, listing)
        return self.store.orders.save(oid, order)

    def directories(self) -> dict[str, Any]:
        return {
            "suppliers": [s for s in self.store.suppliers.list_all()],
            "buyers": [b for b in self.store.buyers.list_all()],
        }

    def status(self) -> dict[str, Any]:
        return {
            "listings": self.store.listings.count(),
            "orders": self.store.orders.count(),
            "suppliers": self.store.suppliers.count(),
            "buyers": self.store.buyers.count(),
        }


class FarmRegistry:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def create_farm(self, *, name: str, owner: str = "", region: str = "", hectares: float = 0.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("farm name required")
        fid = _id("ae_farm")
        return self.store.farms.save(
            fid,
            {
                "farm_id": fid,
                "name": name,
                "owner": owner,
                "region": region,
                "hectares": float(hectares),
                "created_at": _now(),
            },
        )

    def create_company(self, *, name: str, company_type: str = "agribusiness") -> dict[str, Any]:
        if not name:
            raise ValidationError("company name required")
        cid = _id("ae_co")
        return self.store.companies.save(
            cid, {"company_id": cid, "name": name, "company_type": company_type, "created_at": _now()}
        )

    def register_farmland(self, *, farm_id: str, label: str, hectares: float) -> dict[str, Any]:
        if self.store.farms.get(farm_id) is None:
            raise NotFoundError("farm", farm_id)
        lid = _id("ae_land")
        return self.store.farmland.save(
            lid,
            {"land_id": lid, "farm_id": farm_id, "label": label, "hectares": float(hectares), "created_at": _now()},
        )

    def register_storage(self, *, farm_id: str, name: str, capacity_t: float = 0.0) -> dict[str, Any]:
        if self.store.farms.get(farm_id) is None:
            raise NotFoundError("farm", farm_id)
        sid = _id("ae_stor")
        return self.store.storage.save(
            sid,
            {"storage_id": sid, "farm_id": farm_id, "name": name, "capacity_t": float(capacity_t), "created_at": _now()},
        )

    def register_equipment(self, *, farm_id: str, name: str, equipment_type: str = "tractor") -> dict[str, Any]:
        if self.store.farms.get(farm_id) is None:
            raise NotFoundError("farm", farm_id)
        eid = _id("ae_eq")
        return self.store.equipment.save(
            eid,
            {
                "equipment_id": eid,
                "farm_id": farm_id,
                "name": name,
                "equipment_type": equipment_type,
                "created_at": _now(),
            },
        )

    def register_livestock(self, *, farm_id: str, species: str, headcount: int = 0) -> dict[str, Any]:
        if self.store.farms.get(farm_id) is None:
            raise NotFoundError("farm", farm_id)
        lid = _id("ae_live")
        return self.store.livestock.save(
            lid,
            {
                "livestock_id": lid,
                "farm_id": farm_id,
                "species": species,
                "headcount": int(headcount),
                "created_at": _now(),
            },
        )

    def add_certification(self, *, farm_id: str, standard: str, status: str = "active") -> dict[str, Any]:
        if self.store.farms.get(farm_id) is None:
            raise NotFoundError("farm", farm_id)
        cid = _id("ae_cert")
        return self.store.certifications.save(
            cid,
            {
                "certification_id": cid,
                "farm_id": farm_id,
                "standard": standard,
                "status": status,
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "farms": self.store.farms.count(),
            "companies": self.store.companies.count(),
            "farmland": self.store.farmland.count(),
            "equipment": self.store.equipment.count(),
            "certifications": self.store.certifications.count(),
        }
