"""Analytics, integrations, and executive dashboards — Sprint 13.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

REPORT_TYPES = ["market", "price", "sales", "inventory", "demand_forecast", "profit"]
CHANNELS = [
    "telegram",
    "whatsapp",
    "email",
    "vin_databases",
    "government_registries",
    "bank_apis",
    "insurance_apis",
    "gps",
]
DASHBOARD_TYPES = ["dealer", "sales", "inventory", "financial", "ai_insights"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AnalyticsSuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def generate(self, *, report_type: str, title: str = "") -> dict[str, Any]:
        if report_type not in REPORT_TYPES:
            raise ValidationError(f"report_type must be one of {REPORT_TYPES}")
        vehicles = self.store.ea_vehicles.list_all()
        sales = self.store.ea_sales.list_all()
        inventory = self.store.ea_inventory.list_all()
        if report_type == "market":
            metrics: dict[str, Any] = {
                "listed": len(vehicles),
                "avg_price": round(sum(float(v.get("price") or 0) for v in vehicles) / max(1, len(vehicles)), 2),
            }
        elif report_type == "price":
            prices = [float(v.get("price") or 0) for v in vehicles]
            metrics = {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "avg": round(sum(prices) / max(1, len(prices)), 2),
            }
        elif report_type == "sales":
            metrics = {
                "transactions": len(sales),
                "revenue": round(sum(float(s.get("amount") or 0) for s in sales), 2),
            }
        elif report_type == "inventory":
            by_status: dict[str, int] = {}
            for item in inventory:
                st = item.get("status", "unknown")
                by_status[st] = by_status.get(st, 0) + 1
            metrics = {"by_status": by_status, "total": len(inventory)}
        elif report_type == "demand_forecast":
            metrics = {"forecast_units": max(3, self.store.ea_leads.count() + 2), "horizon_days": 30}
        else:
            revenue = sum(float(s.get("amount") or 0) for s in sales)
            cost = revenue * 0.72
            metrics = {"revenue": round(revenue, 2), "cost": round(cost, 2), "profit": round(revenue - cost, 2)}
        rid = _id("earpt")
        report = {
            "report_id": rid,
            "report_type": report_type,
            "title": title or f"{report_type} report",
            "metrics": metrics,
            "generated_at": _now(),
        }
        return self.store.ea_reports.save(rid, report)

    def list_reports(self, report_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.ea_reports.list_all()
        if report_type:
            return [r for r in items if r.get("report_type") == report_type]
        return items

    def status(self) -> dict[str, Any]:
        return {"reports": self.store.ea_reports.count(), "report_types": REPORT_TYPES}


class IntegrationChannels:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.channels = list(CHANNELS)

    def connect(self, *, channel: str, endpoint: str = "", credentials: dict[str, Any] | None = None) -> dict[str, Any]:
        if channel not in self.channels:
            raise ValidationError(f"channel must be one of {self.channels}")
        iid = _id("eaint")
        record = {
            "integration_id": iid,
            "channel": channel,
            "endpoint": endpoint,
            "credentials_present": bool(credentials),
            "status": "connected",
            "connected_at": _now(),
        }
        return self.store.ea_integrations.save(iid, record)

    def dispatch(self, *, channel: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if channel not in self.channels:
            raise ValidationError(f"channel must be one of {self.channels}")
        did = _id("eadisp")
        event = {
            "dispatch_id": did,
            "channel": channel,
            "payload": payload or {},
            "status": "delivered",
            "at": _now(),
        }
        return self.store.ea_integrations.save(did, event)

    def list_connections(self) -> list[dict[str, Any]]:
        return [i for i in self.store.ea_integrations.list_all() if i.get("status") == "connected"]

    def status(self) -> dict[str, Any]:
        return {
            "records": self.store.ea_integrations.count(),
            "channels": self.channels,
            "connected": len(self.list_connections()),
        }


class ExecutiveDashboard:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str, dealer_id: str = "") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        vehicles = self.store.ea_vehicles.list_all()
        sales = self.store.ea_sales.list_all()
        if dealer_id:
            vehicles = [v for v in vehicles if v.get("dealer_id") == dealer_id]
            sales = [s for s in sales if s.get("dealer_id") == dealer_id]
        if dashboard_type == "dealer":
            widgets: dict[str, Any] = {
                "dealers": self.store.ea_dealers.count(),
                "inventory": len(vehicles),
                "open_leads": len([l for l in self.store.ea_leads.list_all() if l.get("stage") not in ("won", "lost")]),
            }
        elif dashboard_type == "sales":
            widgets = {
                "transactions": len(sales),
                "revenue": round(sum(float(s.get("amount") or 0) for s in sales), 2),
            }
        elif dashboard_type == "inventory":
            widgets = {
                "in_stock": len([i for i in self.store.ea_inventory.list_all() if i.get("status") == "in_stock"]),
                "sold": len([i for i in self.store.ea_inventory.list_all() if i.get("status") == "sold"]),
            }
        elif dashboard_type == "financial":
            revenue = sum(float(s.get("amount") or 0) for s in sales)
            widgets = {"revenue": round(revenue, 2), "margin_est": round(revenue * 0.28, 2)}
        else:
            widgets = {
                "ai_runs": self.store.ea_ai_results.count(),
                "fraud_flags": len(
                    [
                        r
                        for r in self.store.ea_ai_results.list_all()
                        if r.get("capability") == "fraud_detection" and r.get("fraudulent")
                    ]
                ),
                "price_estimates": len(
                    [r for r in self.store.ea_ai_results.list_all() if r.get("capability") == "market_price"]
                ),
            }
        did = _id("eadash")
        board = {
            "dashboard_id": did,
            "dashboard_type": dashboard_type,
            "dealer_id": dealer_id,
            "widgets": widgets,
            "rendered_at": _now(),
        }
        return self.store.ea_dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ea_dashboards.count(), "types": self.types}
