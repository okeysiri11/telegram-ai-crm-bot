"""Communications dashboards and analytics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CommunicationsDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.comm_dashboard_types)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        dt = dashboard_type.lower().strip()
        if dt not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "delivery": {
                "deliveries": self.store.comm_deliveries.count(),
                "retries": self.store.comm_retries.count(),
                "messages": self.store.comm_messages.count(),
            },
            "queue": {
                "queued": self.store.comm_queue.count(),
                "events": self.store.comm_events.count(),
                "routes": self.store.comm_routes.count(),
            },
            "channels": {
                "messages": self.store.comm_messages.count(),
                "chat": self.store.comm_chat.count(),
            },
            "audit": {"entries": self.store.comm_audit.count()},
            "analytics": {
                "events": self.store.comm_events.count(),
                "priorities": self.store.comm_priorities.count(),
                "templates": self.store.comm_templates.count(),
                "renders": self.store.comm_renders.count(),
                "deliveries": self.store.comm_deliveries.count(),
            },
        }.get(dt, {})
        did = _id("comm_dash")
        return self.store.comm_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dt,
                "metrics": metrics,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.comm_dashboards.count(), "types": self.types}
