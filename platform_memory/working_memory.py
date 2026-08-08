"""Epic 45.2 — Level 2 Working Memory (today's tasks & unfinished work)."""

from __future__ import annotations

import time
from typing import Any

from platform_memory.continuity_store import MemoryRecord, TimelineEvent, continuity_store, new_id
from platform_memory.memory_permissions import MemoryPrincipal, can_write


class WorkingMemory:
    """Active work for the current day across all channels."""

    def add_task(
        self,
        principal: MemoryPrincipal,
        *,
        title: str,
        content: str = "",
        project_id: str | None = None,
        channel: str = "web",
        status: str = "open",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if not can_write(principal):
            return {"error": "forbidden"}
        rec = MemoryRecord(
            id=new_id("task"),
            owner_id=principal.owner_id,
            company_id=principal.company_id,
            level="working",
            kind="task",
            title=title,
            content=content or title,
            channel=channel,
            project_id=project_id,
            role=principal.role,
            tags=list(tags or []),
            metadata={"status": status},
        )
        continuity_store.save(rec)
        continuity_store.add_timeline(
            TimelineEvent(
                id=new_id("tl"),
                owner_id=principal.owner_id,
                company_id=principal.company_id,
                action="task_created",
                title=title,
                channel=channel,
                project_id=project_id,
                ref_id=rec.id,
            )
        )
        return rec.to_dict()

    def upsert_project(
        self,
        principal: MemoryPrincipal,
        *,
        project_id: str,
        title: str,
        content: str = "",
        channel: str = "web",
        status: str = "active",
    ) -> dict[str, Any]:
        if not can_write(principal):
            return {"error": "forbidden"}
        existing = [
            r
            for r in continuity_store.list_for(principal.owner_id, level="project", kind="project")
            if r.project_id == project_id
        ]
        if existing:
            rec = existing[0]
            rec.title = title
            rec.content = content or title
            rec.metadata["status"] = status
            rec.channel = channel
            continuity_store.save(rec)
            return rec.to_dict()
        rec = MemoryRecord(
            id=new_id("proj"),
            owner_id=principal.owner_id,
            company_id=principal.company_id,
            level="project",
            kind="project",
            title=title,
            content=content or title,
            channel=channel,
            project_id=project_id,
            role=principal.role,
            metadata={"status": status},
        )
        continuity_store.save(rec)
        return rec.to_dict()

    def open_tasks(self, principal: MemoryPrincipal, *, limit: int = 50) -> list[dict[str, Any]]:
        day_ago = time.time() - 86400
        items = continuity_store.list_for(principal.owner_id, company_id=principal.company_id, level="working", kind="task", limit=limit)
        return [
            r.to_dict()
            for r in items
            if r.metadata.get("status", "open") != "done" and r.updated_at >= day_ago - 7 * 86400
        ]

    def unfinished(self, principal: MemoryPrincipal, *, limit: int = 30) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for level, kind in (("working", "task"), ("project", "project"), ("working", "generation"), ("working", "document")):
            for r in continuity_store.list_for(
                principal.owner_id, company_id=principal.company_id, level=level, kind=kind, limit=limit
            ):
                if r.metadata.get("status") in ("done", "closed", "published"):
                    continue
                out.append(r.to_dict())
        out.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        return out[:limit]

    def mark_done(self, principal: MemoryPrincipal, memory_id: str) -> dict[str, Any] | None:
        rec = continuity_store.get(memory_id)
        if not rec or rec.owner_id != principal.owner_id:
            return None
        rec.metadata["status"] = "done"
        continuity_store.save(rec)
        return rec.to_dict()


working_memory = WorkingMemory()
