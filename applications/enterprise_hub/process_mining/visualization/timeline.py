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



class TimelineViz:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def render(self, *, process_id: str) -> dict[str, Any]:
        events = [e for e in self.store.epm_normalized.list_all()]
        # approximate: all events ordered
        timeline = sorted(
            [{"activity": e.get("activity"), "case_id": e.get("case_id"), "ts": e.get("ts")} for e in events],
            key=lambda x: x.get("ts") or "",
        )[:50]
        tid = _id("epm_tl")
        return self.store.epm_visualizations.save(
            tid,
            {"visualization_id": tid, "kind": "timeline", "process_id": process_id, "events": timeline, "at": _now()},
        )
