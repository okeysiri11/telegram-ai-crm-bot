"""Sales AI, analytics, integrations — Sprint 13.3."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

DASHBOARD_TYPES = ["sales", "inventory", "trade_in", "profit", "marketing", "ai_insights"]
INTEGRATION_TARGETS = [
    "vin_intelligence",
    "inspection_ai",
    "digital_passport",
    "marketplace",
    "executive_dashboard",
    "workflow_studio",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SalesAI:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def qualify_lead(self, *, lead_id: str, budget: float = 0.0, intent: str = "browse") -> dict[str, Any]:
        lead = self.store.dc_leads.get(lead_id)
        if lead is None:
            raise ValidationError(f"lead not found: {lead_id}")
        score = 40.0
        if budget >= 15000:
            score += 25
        if intent in ("buy", "trade_in"):
            score += 25
        if lead.get("source") in ("referral", "walk_in"):
            score += 10
        qualified = score >= 60
        rid = _id("dcrm_sq")
        result = {
            "qualification_id": rid,
            "lead_id": lead_id,
            "score": min(100.0, score),
            "qualified": qualified,
            "intent": intent,
            "budget": budget,
            "next_best_action": "schedule_appointment" if qualified else "nurture_email",
            "at": _now(),
        }
        return self.store.dc_sales_ai.save(rid, result)

    def predict_intent(self, *, customer_id: str, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = signals or {}
        views = int(signals.get("vehicle_views", 0))
        messages = int(signals.get("messages", 0))
        intent = "buy" if views >= 5 or messages >= 3 else "browse"
        confidence = min(0.95, 0.4 + views * 0.08 + messages * 0.1)
        rid = _id("dcrm_intent")
        result = {
            "prediction_id": rid,
            "customer_id": customer_id,
            "intent": intent,
            "confidence": round(confidence, 2),
            "at": _now(),
        }
        return self.store.dc_sales_ai.save(rid, result)

    def negotiate(self, *, list_price: float, customer_offer: float) -> dict[str, Any]:
        gap = float(list_price) - float(customer_offer)
        counter = round(float(customer_offer) + gap * 0.45, 2)
        rid = _id("dcrm_neg")
        result = {
            "negotiation_id": rid,
            "list_price": list_price,
            "customer_offer": customer_offer,
            "suggested_counter": counter,
            "upsell": ["extended_warranty", "detailing_package"],
            "cross_sell": ["finance", "insurance"],
            "at": _now(),
        }
        return self.store.dc_sales_ai.save(rid, result)

    def forecast(self, *, dealership_id: str = "", horizon_days: int = 30) -> dict[str, Any]:
        leads = self.store.dc_leads.count()
        sold = len([i for i in self.store.dc_inventory.list_all() if i.get("status") == "sold"])
        forecast_units = max(1, int(leads * 0.25 + sold * 0.5))
        rid = _id("dcrm_fc")
        result = {
            "forecast_id": rid,
            "dealership_id": dealership_id,
            "horizon_days": horizon_days,
            "forecast_units": forecast_units,
            "dealer_performance_score": min(100.0, 55 + leads * 2 + sold * 5),
            "at": _now(),
        }
        return self.store.dc_sales_ai.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"insights": self.store.dc_sales_ai.count()}


class DealerAnalytics:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str, dealership_id: str = "") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        inventory = self.store.dc_inventory.list_all()
        if dealership_id:
            inventory = [i for i in inventory if i.get("dealership_id") == dealership_id]
        if dashboard_type == "sales":
            widgets: dict[str, Any] = {
                "leads": self.store.dc_leads.count(),
                "won": len([l for l in self.store.dc_leads.list_all() if l.get("stage") == "won"]),
            }
        elif dashboard_type == "inventory":
            widgets = {
                "available": len([i for i in inventory if i.get("status") == "available"]),
                "reserved": len([i for i in inventory if i.get("status") == "reserved"]),
            }
        elif dashboard_type == "trade_in":
            widgets = {
                "evaluations": self.store.dc_tradeins.count(),
                "offers": self.store.dc_tradein_offers.count(),
            }
        elif dashboard_type == "profit":
            offers = self.store.dc_tradeins.list_all()
            margin = round(sum(float(o.get("dealer_margin") or 0) for o in offers), 2)
            widgets = {"trade_in_margin": margin, "evaluations": len(offers)}
        elif dashboard_type == "marketing":
            widgets = {
                "contacts": self.store.dc_contacts.count(),
                "appointments": self.store.dc_appointments.count(),
            }
        else:
            widgets = {
                "sales_ai": self.store.dc_sales_ai.count(),
                "optimizations": self.store.dc_optimizations.count(),
                "recommendations": self.store.dc_recommendations.count(),
            }
        did = _id("dcrm_dash")
        board = {
            "dashboard_id": did,
            "dashboard_type": dashboard_type,
            "dealership_id": dealership_id,
            "widgets": widgets,
            "rendered_at": _now(),
        }
        return self.store.dc_dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.dc_dashboards.count(), "types": self.types}


class DealerIntegrations:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.targets = list(INTEGRATION_TARGETS)

    def connect(self, *, target: str, endpoint: str = "") -> dict[str, Any]:
        if target not in self.targets:
            raise ValidationError(f"target must be one of {self.targets}")
        iid = _id("dcrm_int")
        record = {
            "integration_id": iid,
            "target": target,
            "endpoint": endpoint,
            "status": "connected",
            "connected_at": _now(),
        }
        return self.store.dc_integrations.save(iid, record)

    def list_connections(self) -> list[dict[str, Any]]:
        return [i for i in self.store.dc_integrations.list_all() if i.get("status") == "connected"]

    def status(self) -> dict[str, Any]:
        return {"connected": len(self.list_connections()), "targets": self.targets}
