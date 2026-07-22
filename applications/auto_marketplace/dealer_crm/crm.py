"""Dealer CRM core — dealership, pipeline, leads, contacts — Sprint 13.3."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

PIPELINE_STAGES = ["new", "contacted", "qualified", "appointment", "negotiation", "won", "lost"]
CONTACT_CHANNELS = ["call", "email", "messenger", "sms", "in_person"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DealerCRM:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create_dealership(self, *, name: str, region: str = "", contact: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("dealership name required")
        did = _id("dcrm_dship")
        item = {
            "dealership_id": did,
            "name": name,
            "region": region,
            "contact": contact,
            "status": "active",
            "created_at": _now(),
        }
        return self.store.dc_dealerships.save(did, item)

    def create_customer(self, *, name: str, email: str = "", phone: str = "", dealership_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("customer name required")
        cid = _id("dcrm_cust")
        profile = {
            "customer_id": cid,
            "name": name,
            "email": email,
            "phone": phone,
            "dealership_id": dealership_id,
            "created_at": _now(),
        }
        return self.store.dc_customers.save(cid, profile)

    def create_lead(
        self,
        *,
        name: str,
        interest: str = "",
        source: str = "web",
        dealership_id: str = "",
        customer_id: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("lead name required")
        lid = _id("dcrm_lead")
        lead = {
            "lead_id": lid,
            "name": name,
            "interest": interest,
            "source": source,
            "dealership_id": dealership_id,
            "customer_id": customer_id,
            "stage": "new",
            "created_at": _now(),
        }
        return self.store.dc_leads.save(lid, lead)

    def advance_pipeline(self, lead_id: str, *, stage: str) -> dict[str, Any]:
        lead = self.store.dc_leads.get(lead_id)
        if lead is None:
            raise NotFoundError("lead", lead_id)
        if stage not in PIPELINE_STAGES:
            raise ValidationError(f"stage must be one of {PIPELINE_STAGES}")
        lead["stage"] = stage
        lead["updated_at"] = _now()
        return self.store.dc_leads.save(lead_id, lead)

    def log_contact(
        self,
        *,
        channel: str,
        related_id: str,
        summary: str,
        direction: str = "outbound",
    ) -> dict[str, Any]:
        if channel not in CONTACT_CHANNELS:
            raise ValidationError(f"channel must be one of {CONTACT_CHANNELS}")
        cid = _id("dcrm_contact")
        record = {
            "contact_id": cid,
            "channel": channel,
            "related_id": related_id,
            "summary": summary,
            "direction": direction,
            "at": _now(),
        }
        saved = self.store.dc_contacts.save(cid, record)
        if channel == "call":
            self.store.dc_call_log.save(cid, {**record, "log_type": "call"})
        elif channel == "email":
            self.store.dc_email_log.save(cid, {**record, "log_type": "email"})
        return saved

    def create_task(self, *, title: str, assignee: str = "", due_at: str = "", related_id: str = "") -> dict[str, Any]:
        if not title:
            raise ValidationError("task title required")
        tid = _id("dcrm_task")
        task = {
            "task_id": tid,
            "title": title,
            "assignee": assignee,
            "due_at": due_at,
            "related_id": related_id,
            "status": "open",
            "created_at": _now(),
        }
        return self.store.dc_tasks.save(tid, task)

    def schedule_appointment(
        self,
        *,
        title: str,
        starts_at: str,
        ends_at: str = "",
        customer_id: str = "",
        dealership_id: str = "",
    ) -> dict[str, Any]:
        if not title or not starts_at:
            raise ValidationError("title and starts_at required")
        aid = _id("dcrm_appt")
        appt = {
            "appointment_id": aid,
            "title": title,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "customer_id": customer_id,
            "dealership_id": dealership_id,
            "status": "scheduled",
            "created_at": _now(),
        }
        self.store.dc_calendar.save(aid, {"event_id": aid, "kind": "appointment", **appt})
        return self.store.dc_appointments.save(aid, appt)

    def pipeline_snapshot(self) -> dict[str, Any]:
        counts = {s: 0 for s in PIPELINE_STAGES}
        for lead in self.store.dc_leads.list_all():
            stage = lead.get("stage", "new")
            if stage in counts:
                counts[stage] += 1
        return {"pipeline": counts, "total_leads": self.store.dc_leads.count()}

    def status(self) -> dict[str, Any]:
        return {
            "dealerships": self.store.dc_dealerships.count(),
            "customers": self.store.dc_customers.count(),
            "leads": self.store.dc_leads.count(),
            "contacts": self.store.dc_contacts.count(),
            "tasks": self.store.dc_tasks.count(),
            "appointments": self.store.dc_appointments.count(),
        }
