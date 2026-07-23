"""Subscription manager — module subscriptions to event types."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.event_platform.models import SUBSCRIBER_KINDS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SubscriptionManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def subscribe(
        self,
        *,
        subscriber: str,
        event_types: list[str],
        filter_severity: str | None = None,
    ) -> dict[str, Any]:
        if not subscriber:
            raise ValidationError("subscriber is required")
        if not event_types:
            raise ValidationError("event_types required")
        sid = _id("evp_sub")
        return self.store.evp_subscriptions.save(
            sid,
            {
                "subscription_id": sid,
                "subscriber": subscriber,
                "event_types": event_types,
                "filter_severity": filter_severity,
                "active": True,
                "at": _now(),
            },
        )

    def for_event(self, *, event_type: str, severity: str | None = None) -> list[dict[str, Any]]:
        out = []
        for s in self.store.evp_subscriptions.list_all():
            if not s.get("active"):
                continue
            if event_type not in (s.get("event_types") or []):
                continue
            filt = s.get("filter_severity")
            if filt and severity and filt != severity:
                continue
            out.append(s)
        return out

    def status(self) -> dict[str, Any]:
        return {
            "subscriptions": self.store.evp_subscriptions.count(),
            "kinds": list(SUBSCRIBER_KINDS),
        }
