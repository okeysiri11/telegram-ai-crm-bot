"""Epic 45.2 — AI Timeline (today / yesterday / week / month)."""

from __future__ import annotations

import time
from typing import Any

from platform_memory.continuity_store import TimelineEvent, continuity_store, new_id
from platform_memory.memory_permissions import MemoryPrincipal


WINDOWS = {
    "today": 86400,
    "yesterday": 172800,
    "week": 7 * 86400,
    "month": 30 * 86400,
    "all": None,
}


class MemoryTimeline:
    def record(
        self,
        principal: MemoryPrincipal,
        *,
        action: str,
        title: str,
        channel: str = "web",
        project_id: str | None = None,
        ref_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ev = TimelineEvent(
            id=new_id("tl"),
            owner_id=principal.owner_id,
            company_id=principal.company_id,
            action=action,
            title=title,
            channel=channel,
            project_id=project_id,
            ref_id=ref_id,
            metadata=dict(metadata or {}),
        )
        continuity_store.add_timeline(ev)
        return ev.to_dict()

    def view(
        self,
        principal: MemoryPrincipal,
        *,
        window: str = "today",
        limit: int = 100,
    ) -> dict[str, Any]:
        now = time.time()
        win = WINDOWS.get(window, WINDOWS["today"])
        if window == "yesterday":
            since, until = now - 2 * 86400, now - 86400
        elif win is None:
            since, until = None, None
        else:
            since, until = now - win, None
        events = continuity_store.list_timeline(
            principal.owner_id,
            company_id=principal.company_id,
            since=since,
            until=until,
            limit=limit,
        )
        return {
            "window": window,
            "count": len(events),
            "events": [e.to_dict() for e in events],
            "windows": list(WINDOWS.keys()),
        }


memory_timeline = MemoryTimeline()
