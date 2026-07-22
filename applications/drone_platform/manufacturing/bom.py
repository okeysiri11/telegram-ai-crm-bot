"""Bill of Materials — engineering/manufacturing/assembly BOMs (Sprint 11.6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.inventory.service import InventoryService, inventory_service
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


BOM_TYPES = ("engineering", "manufacturing", "assembly")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BOMManager:
    def __init__(self, store: DroneStore | None = None, inventory: InventoryService | None = None) -> None:
        self.store = store or drone_store
        self.inventory = inventory or inventory_service

    def create(
        self,
        *,
        name: str,
        bom_type: str = "manufacturing",
        version: str = "1.0",
        lines: list[dict[str, Any]] | None = None,
        alternatives: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        bom_type = bom_type.lower().strip()
        if bom_type not in BOM_TYPES:
            raise ValidationError(f"Unsupported BOM type: {bom_type}")
        bid = f"bom_{uuid.uuid4().hex[:12]}"
        bom = {
            "bom_id": bid,
            "name": name,
            "bom_type": bom_type,
            "version": version,
            "lines": list(lines or []),
            "alternatives": dict(alternatives or {}),
            "versions": [{"version": version, "at": _now()}],
            "created_at": _now(),
        }
        self.store.boms.save(bid, bom)
        return bom

    def get(self, bom_id: str) -> dict[str, Any]:
        item = self.store.boms.get(bom_id)
        if item is None:
            raise NotFoundError("bom", bom_id)
        return item

    def list(self, *, bom_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.boms.list_all()
        if bom_type:
            return [b for b in items if b.get("bom_type") == bom_type]
        return items

    def version_bom(self, bom_id: str, *, version: str, lines: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        bom = self.get(bom_id)
        bom["version"] = version
        if lines is not None:
            bom["lines"] = list(lines)
        bom["versions"].append({"version": version, "at": _now()})
        self.store.boms.save(bom_id, bom)
        return bom

    def cost_calculator(self, bom_id: str) -> dict[str, Any]:
        bom = self.get(bom_id)
        total = 0.0
        details = []
        for line in bom.get("lines") or []:
            qty = float(line.get("qty", 1))
            unit = float(line.get("unit_cost", 0))
            cost = qty * unit
            total += cost
            details.append({"sku": line.get("sku"), "qty": qty, "unit_cost": unit, "line_cost": round(cost, 2)})
        return {"bom_id": bom_id, "total_cost": round(total, 2), "currency": "USD", "lines": details}

    def availability_checker(self, bom_id: str, *, warehouse_id: str | None = None) -> dict[str, Any]:
        bom = self.get(bom_id)
        stock = self.inventory.list_stock(warehouse_id)
        by_sku: dict[str, int] = {}
        for s in stock:
            by_sku[s.sku] = by_sku.get(s.sku, 0) + int(s.quantity)
        missing = []
        available = []
        for line in bom.get("lines") or []:
            sku = str(line.get("sku", ""))
            need = int(line.get("qty", 1))
            have = by_sku.get(sku, 0)
            row = {"sku": sku, "required": need, "available": have, "ok": have >= need}
            if have >= need:
                available.append(row)
            else:
                missing.append(row)
        return {"bom_id": bom_id, "fully_available": not missing, "available": available, "missing": missing}

    def procurement_suggestions(self, bom_id: str, *, warehouse_id: str | None = None) -> dict[str, Any]:
        check = self.availability_checker(bom_id, warehouse_id=warehouse_id)
        suggestions = []
        for m in check["missing"]:
            suggestions.append(
                {
                    "sku": m["sku"],
                    "order_qty": max(0, m["required"] - m["available"]),
                    "reason": "insufficient_stock",
                }
            )
        return {"bom_id": bom_id, "suggestions": suggestions, "count": len(suggestions)}

    def status(self) -> dict[str, Any]:
        return {
            "bom_manager": "1.0",
            "bom_types": list(BOM_TYPES),
            "bom_count": self.store.boms.count(),
            "capabilities": [
                "engineering_bom",
                "manufacturing_bom",
                "assembly_bom",
                "versioned_bom",
                "alternative_components",
                "cost_calculator",
                "availability_checker",
                "procurement_suggestions",
            ],
        }


bom_manager = BOMManager()
