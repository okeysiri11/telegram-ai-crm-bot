"""Ownership assistant, personal assistant, dashboards — Sprint 13.4."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

ASSISTANT_MODES = ["voice", "chat", "purchase", "maintenance", "emergency", "trip"]
DASHBOARD_TYPES = ["buyer", "purchase", "ownership", "savings"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class OwnershipAssistant:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create_plan(self, *, buyer_id: str, vin: str, purchase_date: str = "") -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if not buyer_id or len(vin) < 11:
            raise ValidationError("buyer_id and vin required")
        oid = _id("bai_own")
        plan = {
            "ownership_id": oid,
            "buyer_id": buyer_id,
            "vin": vin,
            "purchase_date": purchase_date or _now(),
            "service_schedule": [
                {"at_miles": 10000, "tasks": ["oil_change", "inspection"]},
                {"at_miles": 40000, "tasks": ["brakes", "fluids"]},
            ],
            "maintenance_reminders": [],
            "warranty": {"status": "active", "expires_at": ""},
            "insurance_renewal": {"due_at": "", "status": "unknown"},
            "registration": {"status": "pending"},
            "document_vault": [],
            "timeline": [{"event": "ownership_started", "at": _now()}],
            "created_at": _now(),
        }
        return self.store.ba_ownership.save(oid, plan)

    def add_reminder(self, ownership_id: str, *, title: str, due_at: str) -> dict[str, Any]:
        plan = self.store.ba_ownership.get(ownership_id)
        if plan is None:
            raise NotFoundError("ownership", ownership_id)
        reminder = {"reminder_id": _id("bai_rem"), "title": title, "due_at": due_at, "status": "scheduled"}
        plan.setdefault("maintenance_reminders", []).append(reminder)
        plan["timeline"].append({"event": "reminder_added", "title": title, "at": _now()})
        self.store.ba_ownership.save(ownership_id, plan)
        return reminder

    def store_document(self, ownership_id: str, *, name: str, doc_type: str = "general") -> dict[str, Any]:
        plan = self.store.ba_ownership.get(ownership_id)
        if plan is None:
            raise NotFoundError("ownership", ownership_id)
        doc = {"doc_id": _id("bai_doc"), "name": name, "doc_type": doc_type, "stored_at": _now()}
        plan.setdefault("document_vault", []).append(doc)
        self.store.ba_ownership.save(ownership_id, plan)
        return doc

    def status(self) -> dict[str, Any]:
        return {"ownership_plans": self.store.ba_ownership.count()}


class PersonalAssistant:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.modes = list(ASSISTANT_MODES)

    def ask(self, *, mode: str, message: str, buyer_id: str = "") -> dict[str, Any]:
        if mode not in self.modes:
            raise ValidationError(f"mode must be one of {self.modes}")
        if not message:
            raise ValidationError("message required")
        replies = {
            "purchase": "Based on your budget, prioritize inspected listings with clean VIN history.",
            "maintenance": "Schedule oil service every 10,000 km and track warranty deadlines.",
            "emergency": "If unsafe to drive, call roadside assistance and document the incident.",
            "trip": "Check tire pressure, fluids, and insurance card before departure.",
            "voice": f"Heard: {message[:80]}. I can help with purchase or maintenance next.",
            "chat": f"Got it — {message[:100]}. Want search, negotiate, or ownership help?",
        }
        rid = _id("bai_asst")
        result = {
            "response_id": rid,
            "mode": mode,
            "buyer_id": buyer_id,
            "message": message,
            "reply": replies.get(mode, "How can I help with your vehicle journey?"),
            "at": _now(),
        }
        return self.store.ba_assistant.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"responses": self.store.ba_assistant.count(), "modes": self.modes}


class BuyerDashboard:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str, buyer_id: str = "") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        if dashboard_type == "buyer":
            widgets: dict[str, Any] = {
                "profiles": self.store.ba_profiles.count(),
                "searches": self.store.ba_searches.count(),
            }
        elif dashboard_type == "purchase":
            widgets = {
                "negotiations": self.store.ba_negotiations.count(),
                "purchase_analyses": self.store.ba_purchase_intel.count(),
                "protection_checks": self.store.ba_protection.count(),
            }
        elif dashboard_type == "ownership":
            widgets = {
                "ownership_plans": self.store.ba_ownership.count(),
                "assistant_replies": self.store.ba_assistant.count(),
            }
        else:
            analyses = self.store.ba_purchase_intel.list_all()
            savings = round(sum(float(a.get("list_price", a.get("price", 0)) or 0) * 0.05 for a in analyses), 2)
            widgets = {"estimated_negotiation_savings": savings, "analyses": len(analyses)}
        did = _id("bai_dash")
        board = {
            "dashboard_id": did,
            "dashboard_type": dashboard_type,
            "buyer_id": buyer_id,
            "widgets": widgets,
            "rendered_at": _now(),
        }
        return self.store.ba_dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ba_dashboards.count(), "types": self.types}
