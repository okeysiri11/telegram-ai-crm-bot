"""CRM suite — Sprint 13.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

FUNNEL_STAGES = ["new", "contacted", "qualified", "negotiation", "won", "lost"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CRMSuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create_lead(
        self,
        *,
        name: str,
        interest: str = "",
        source: str = "web",
        dealer_id: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("lead name required")
        lid = _id("ealead")
        lead = {
            "lead_id": lid,
            "name": name,
            "interest": interest,
            "source": source,
            "dealer_id": dealer_id,
            "stage": "new",
            "created_at": _now(),
        }
        return self.store.ea_leads.save(lid, lead)

    def advance_funnel(self, lead_id: str, *, stage: str) -> dict[str, Any]:
        lead = self.store.ea_leads.get(lead_id)
        if lead is None:
            raise NotFoundError("lead", lead_id)
        if stage not in FUNNEL_STAGES:
            raise ValidationError(f"stage must be one of {FUNNEL_STAGES}")
        lead["stage"] = stage
        lead["updated_at"] = _now()
        return self.store.ea_leads.save(lead_id, lead)

    def communicate(
        self,
        *,
        channel: str,
        recipient: str,
        message: str,
        related_id: str = "",
    ) -> dict[str, Any]:
        cid = _id("eacomm")
        record = {
            "communication_id": cid,
            "channel": channel,
            "recipient": recipient,
            "message": message,
            "related_id": related_id,
            "status": "sent",
            "at": _now(),
        }
        return self.store.ea_communications.save(cid, record)

    def notify(self, *, recipient: str, title: str, body: str = "") -> dict[str, Any]:
        return self.communicate(channel="notification", recipient=recipient, message=f"{title}: {body}")

    def schedule_followup(self, *, lead_id: str, due_at: str, note: str = "") -> dict[str, Any]:
        if self.store.ea_leads.get(lead_id) is None:
            raise NotFoundError("lead", lead_id)
        fid = _id("eafu")
        item = {
            "followup_id": fid,
            "lead_id": lead_id,
            "due_at": due_at,
            "note": note,
            "status": "scheduled",
            "created_at": _now(),
        }
        return self.store.ea_followups.save(fid, item)

    def funnel_snapshot(self) -> dict[str, Any]:
        counts = {s: 0 for s in FUNNEL_STAGES}
        for lead in self.store.ea_leads.list_all():
            stage = lead.get("stage", "new")
            if stage in counts:
                counts[stage] += 1
        return {"funnel": counts, "total_leads": self.store.ea_leads.count()}

    def status(self) -> dict[str, Any]:
        return {
            "leads": self.store.ea_leads.count(),
            "customers": self.store.ea_customers.count(),
            "dealers": self.store.ea_dealers.count(),
            "communications": self.store.ea_communications.count(),
            "followups": self.store.ea_followups.count(),
        }
