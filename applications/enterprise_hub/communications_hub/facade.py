"""Communications Hub Suite facade — Sprint 22.6 / v6.7.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_communications_hub.facade import CommunicationsHubLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CommunicationsHubSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = CommunicationsHubLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = CommunicationsHubLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("ech_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.ech_bootstraps.save(bid, record)
        tid = _id("ech_tmpl")
        self.store.ech_templates.save(tid, {"template_id": tid, **full["template"], "created_at": _now()})
        aid = _id("ech_auto")
        self.store.ech_automations.save(aid, {"automation_id": aid, **full["automation"], "created_at": _now()})
        mid = _id("ech_msg")
        self.store.ech_messages.save(mid, {"message_id": mid, **full["sent"], "created_at": _now()})
        for kind in ("sent", "opened"):
            eid = _id("ech_tl")
            self.store.ech_timeline.save(
                eid,
                {
                    "event_id": eid,
                    "customer_id": "c1",
                    "kind": kind,
                    "channel": "sms",
                    "created_at": _now(),
                },
            )
        asid = _id("ech_ai")
        self.store.ech_assistant.save(asid, {"assistant_id": asid, **full["assistant"], "created_at": _now()})
        did = _id("ech_dlv")
        self.store.ech_deliveries.save(did, {"delivery_id": did, **full["delivery"], "created_at": _now()})
        anid = _id("ech_an")
        self.store.ech_analytics.save(anid, {"analytics_id": anid, **full["analytics"], "created_at": _now()})
        record["template_id"] = tid
        record["automation_id"] = aid
        record["message_id"] = mid
        self.store.ech_bootstraps.save(bid, record)
        return record

    def send_message(self, **kwargs: Any) -> dict[str, Any]:
        customer_id = kwargs.pop("customer_id", None)
        try:
            result = self.library.center.send(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        mid = _id("ech_msg")
        record = {"message_id": mid, **result, "created_at": _now()}
        self.store.ech_messages.save(mid, record)
        timeline_customer = customer_id or kwargs.get("recipient")
        if timeline_customer:
            eid = _id("ech_tl")
            self.store.ech_timeline.save(
                eid,
                {
                    "event_id": eid,
                    "customer_id": timeline_customer,
                    "kind": "sent",
                    "channel": result["channel"],
                    "payload": {"message_id": mid},
                    "created_at": _now(),
                },
            )
        return record

    def create_template(self, **kwargs: Any) -> dict[str, Any]:
        try:
            tmpl = self.library.templates.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        tid = _id("ech_tmpl")
        record = {"template_id": tid, **tmpl, "created_at": _now()}
        self.store.ech_templates.save(tid, record)
        return record

    def create_automation(self, **kwargs: Any) -> dict[str, Any]:
        try:
            auto = self.library.automation.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        aid = _id("ech_auto")
        record = {"automation_id": aid, **auto, "created_at": _now()}
        self.store.ech_automations.save(aid, record)
        return record

    def timeline(self, *, customer_id: str) -> dict[str, Any]:
        events = [e for e in self.store.ech_timeline.list_all() if e.get("customer_id") == customer_id]
        if not events:
            return self.library.timeline.history(customer_id=customer_id)
        return {"customer_id": customer_id, "events": events, "count": len(events)}

    def assistant(self, *, purpose: str, customer_id: str = "") -> dict[str, Any]:
        result = self.library.assistant.recommend(purpose=purpose, customer_id=customer_id)
        asid = _id("ech_ai")
        record = {"assistant_id": asid, **result, "created_at": _now()}
        self.store.ech_assistant.save(asid, record)
        return record

    def enqueue_campaign(self, **kwargs: Any) -> dict[str, Any]:
        try:
            delivery = self.library.delivery.enqueue(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        did = _id("ech_dlv")
        record = {"delivery_id": did, **delivery, "created_at": _now()}
        self.store.ech_deliveries.save(did, record)
        return record

    def analytics(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.analytics.summarize(**kwargs)
        anid = _id("ech_an")
        record = {"analytics_id": anid, **result, "created_at": _now()}
        self.store.ech_analytics.save(anid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.ech_bootstraps.list_all()),
            "templates": len(self.store.ech_templates.list_all()),
            "messages": len(self.store.ech_messages.list_all()),
            "automations": len(self.store.ech_automations.list_all()),
            "deliveries": len(self.store.ech_deliveries.list_all()),
        }


communications_hub = CommunicationsHubSuite()
