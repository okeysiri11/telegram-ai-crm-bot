from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.command_center.realtime_monitor import RealtimeMonitor


class RealtimeAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.monitor = RealtimeMonitor(self.store)

    def report(self) -> dict[str, Any]:
        snap = self.monitor.snapshot()
        rid = _id("ecc_art")
        record = {"analytics_id": rid, "kind": "realtime", "snapshot": snap, "reported_at": _now()}
        self.store.ecc_analytics.save(rid, record)
        return record
