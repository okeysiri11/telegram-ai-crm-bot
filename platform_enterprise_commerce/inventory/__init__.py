"""Inventory Integration — Sprint 22.7."""

from __future__ import annotations

from typing import Any


class InventoryIntegration:
    def deduct(self, *, sale_lines: list[dict[str, Any]], stock: dict[str, float] | None = None) -> dict[str, Any]:
        stock = dict(stock or {})
        deductions = []
        for line in sale_lines:
            sku = line.get("sku") or line.get("name") or line.get("service_id") or "item"
            qty = float(line.get("qty", 1) or 1)
            # services may consume materials listed under materials
            materials = line.get("materials") or [{"sku": sku, "qty": qty if line.get("kind") == "product" else 0}]
            for mat in materials:
                msku = mat.get("sku", sku)
                mqty = float(mat.get("qty", 0) or 0)
                if mqty <= 0:
                    continue
                before = float(stock.get(msku, 10))
                after = before - mqty
                stock[msku] = after
                deductions.append({"sku": msku, "qty": mqty, "before": before, "after": after})
        low = [d["sku"] for d in deductions if d["after"] <= 2]
        return {
            "deductions": deductions,
            "stock": stock,
            "low_stock": low,
            "purchase_forecast": [{"sku": s, "suggest_qty": 20} for s in low],
            "warehouse_ref": "enterprise_warehouse",
            "auto_deducted": True,
        }
