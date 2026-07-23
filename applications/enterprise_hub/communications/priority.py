"""AI Priority Engine — classify notification urgency."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.communications.models import PRIORITIES, PRIORITY_CHANNEL_MAP
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


_CRITICAL_HINTS = ("server down", "security", "breach", "outage", "critical", "emergency")
_HIGH_HINTS = ("approval", "invoice overdue", "failed", "alert", "urgent")
_LOW_HINTS = ("newsletter", "digest", "report", "weekly")
_SILENT_HINTS = ("telemetry", "heartbeat", "metric", "silent")


class PriorityEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def classify(self, *, subject: str = "", event: str = "", hint: str = "") -> dict[str, Any]:
        text = f"{subject} {event} {hint}".lower()
        priority = "medium"
        if any(h in text for h in _CRITICAL_HINTS):
            priority = "critical"
        elif any(h in text for h in _HIGH_HINTS):
            priority = "high"
        elif any(h in text for h in _SILENT_HINTS):
            priority = "silent"
        elif any(h in text for h in _LOW_HINTS):
            priority = "low"
        pid = _id("comm_prio")
        return self.store.comm_priorities.save(
            pid,
            {
                "priority_id": pid,
                "priority": priority if priority in PRIORITIES else "medium",
                "channels": list(PRIORITY_CHANNEL_MAP.get(priority, ["email"])),
                "subject": subject,
                "event": event,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"classifications": self.store.comm_priorities.count(), "levels": list(PRIORITIES)}
