
"""Executive Dashboard for Auto Marketplace (Sprint 13.0)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import AutoMarketplaceStore, auto_marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AutoDashboard:
    def __init__(self, store: AutoMarketplaceStore | None = None) -> None:
        self.store = store or auto_marketplace_store
        self.types = list(DEFAULT_CONFIG.dashboard_types)

    def render(self, *, dashboard_type: str, dealer_id: str = "") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        vehicles = self.store.vehicles.list_all()
        sales = self.store.sales.list_all()
        if dealer_id:
            vehicles = [v for v in vehicles if v.get("dealer_id") == dealer_id]
            sales = [s for s in sales if s.get("dealer_id") == dealer_id]
        widgets: dict[str, Any]
        if dashboard_type == "dealer":
            widgets = {
                "dealers": len(self.store.dealers.list_all()),
                "inventory": len(vehicles),
                "open_leads": len([l for l in self.store.leads.list_all() if l.get("stage") not in ("won", "lost")]),
            }
        elif dashboard_type == "sales":
            widgets = {
                "transactions": len(sales),
                "revenue": round(sum(float(s.get("amount") or 0) for s in sales), 2),
            }
        elif dashboard_type == "inventory":
            widgets = {
                "in_stock": len([i for i in self.store.inventory.list_all() if i.get("status") == "in_stock"]),
                "sold": len([i for i in self.store.inventory.list_all() if i.get("status") == "sold"]),
            }
        elif dashboard_type == "financial":
            revenue = sum(float(s.get("amount") or 0) for s in sales)
            widgets = {"revenue": round(revenue, 2), "margin_est": round(revenue * 0.28, 2)}
        else:
            widgets = {
                "ai_runs": len(self.store.ai_results.list_all()),
                "fraud_flags": len([r for r in self.store.ai_results.list_all() if r.get("capability") == "fraud_detection" and r.get("fraudulent")]),
                "price_estimates": len([r for r in self.store.ai_results.list_all() if r.get("capability") == "market_price"]),
            }
        did = _id("dash")
        board = {
            "dashboard_id": did,
            "dashboard_type": dashboard_type,
            "dealer_id": dealer_id,
            "widgets": widgets,
            "rendered_at": _now(),
        }
        return self.store.dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": len(self.store.dashboards.list_all()), "types": self.types}


auto_dashboard = AutoDashboard()
