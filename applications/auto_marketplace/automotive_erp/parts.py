"""Parts management — Sprint 13.6."""

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


class PartsManagement:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def add_part(self, *, sku: str, name: str, warehouse: str = "main", qty: int = 0, unit_cost: float = 0.0) -> dict[str, Any]:
        if not sku or not name:
            raise ValidationError("sku and name required")
        pid = _id("erp_part")
        part = {
            "part_id": pid,
            "sku": sku,
            "name": name,
            "warehouse": warehouse,
            "qty": int(qty),
            "unit_cost": float(unit_cost),
            "serials": [],
            "created_at": _now(),
        }
        self.store.erp_warehouses.save(warehouse, {"warehouse_id": warehouse, "name": warehouse, "updated_at": _now()})
        return self.store.erp_parts.save(pid, part)

    def register_supplier(self, *, name: str, contact: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("supplier name required")
        sid = _id("erp_sup")
        supplier = {"supplier_id": sid, "name": name, "contact": contact, "created_at": _now()}
        return self.store.erp_suppliers.save(sid, supplier)

    def create_purchase_order(self, *, supplier_id: str, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if self.store.erp_suppliers.get(supplier_id) is None:
            raise NotFoundError("supplier", supplier_id)
        oid = _id("erp_po")
        order = {
            "purchase_order_id": oid,
            "supplier_id": supplier_id,
            "items": items or [],
            "status": "open",
            "created_at": _now(),
        }
        return self.store.erp_purchase_orders.save(oid, order)

    def reserve(self, *, part_id: str, qty: int, ref: str = "") -> dict[str, Any]:
        part = self.store.erp_parts.get(part_id)
        if part is None:
            raise NotFoundError("part", part_id)
        qty = int(qty)
        if qty < 1 or qty > int(part.get("qty") or 0):
            raise ValidationError("insufficient stock")
        part["qty"] = int(part["qty"]) - qty
        self.store.erp_parts.save(part_id, part)
        rid = _id("erp_res")
        reservation = {
            "reservation_id": rid,
            "part_id": part_id,
            "qty": qty,
            "ref": ref,
            "status": "reserved",
            "at": _now(),
        }
        return self.store.erp_part_reservations.save(rid, reservation)

    def track_serial(self, *, part_id: str, serial: str) -> dict[str, Any]:
        part = self.store.erp_parts.get(part_id)
        if part is None:
            raise NotFoundError("part", part_id)
        part.setdefault("serials", []).append(serial)
        self.store.erp_parts.save(part_id, part)
        return {"part_id": part_id, "serial": serial, "serials": len(part["serials"])}

    def forecast(self, *, warehouse: str = "main") -> dict[str, Any]:
        parts = [p for p in self.store.erp_parts.list_all() if p.get("warehouse") == warehouse]
        low = [p for p in parts if int(p.get("qty") or 0) < 5]
        fid = _id("erp_fc")
        result = {
            "forecast_id": fid,
            "warehouse": warehouse,
            "skus": len(parts),
            "low_stock": len(low),
            "reorder_skus": [p["sku"] for p in low],
            "at": _now(),
        }
        return self.store.erp_inventory_forecasts.save(fid, result)

    def status(self) -> dict[str, Any]:
        return {
            "parts": self.store.erp_parts.count(),
            "suppliers": self.store.erp_suppliers.count(),
            "purchase_orders": self.store.erp_purchase_orders.count(),
            "reservations": self.store.erp_part_reservations.count(),
        }
