"""POS Workspace — Sprint 22.7."""

from __future__ import annotations

from typing import Any


class POSWorkspace:
    def session(self, *, cashier_id: str = "cashier", industry: str = "beauty") -> dict[str, Any]:
        return {
            "cashier_id": cashier_id,
            "industry": industry,
            "features": [
                "quick_sale",
                "product_search",
                "customer_search",
                "qr",
                "barcode",
                "gift_certificates",
                "memberships",
                "discounts",
                "bonuses",
            ],
            "status": "open",
            "fast_checkout": True,
        }

    def lookup(self, *, query: str, catalog: list[dict[str, Any]] | None = None, customers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        q = (query or "").strip().lower()
        if not q:
            raise ValueError("lookup query is required")
        products = [c for c in (catalog or []) if q in str(c.get("name", "")).lower() or q in str(c.get("sku", "")).lower() or q == str(c.get("barcode", "")).lower()]
        people = [c for c in (customers or []) if q in str(c.get("name", "")).lower() or q in str(c.get("phone", "")).lower()]
        return {"query": query, "products": products, "customers": people, "supports_qr_barcode": True}
