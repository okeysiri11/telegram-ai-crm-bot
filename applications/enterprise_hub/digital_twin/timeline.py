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




class TimelineEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def append(
        self,
        *,
        twin_id: str,
        event: str,
        actor: str = "system",
        detail: dict[str, Any] | None = None,
        ai_decision: bool = False,
    ) -> dict[str, Any]:
        if not twin_id or not event:
            raise ValidationError("twin_id and event are required")
        if not self.store.edt_twins.get(twin_id):
            raise NotFoundError(f"twin not found: {twin_id}")
        tid = _id("edt_tl")
        return self.store.edt_timeline.save(
            tid,
            {
                "timeline_id": tid,
                "twin_id": twin_id,
                "event": event,
                "actor": actor,
                "detail": detail or {},
                "ai_decision": ai_decision,
                "at": _now(),
            },
        )

    def history(self, *, twin_id: str) -> list[dict[str, Any]]:
        items = [t for t in self.store.edt_timeline.list_all() if t.get("twin_id") == twin_id]
        twin = self.store.edt_twins.get(twin_id)
        if twin:
            for h in twin.get("history") or []:
                items.append({"twin_id": twin_id, "event": h.get("action"), "at": h.get("at"), "actor": h.get("by"), "from_twin": True})
        return sorted(items, key=lambda x: x.get("at") or "")

    def status(self) -> dict[str, Any]:
        return {"timeline_events": len(self.store.edt_timeline.list_all())}
