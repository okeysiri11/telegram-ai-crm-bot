"""Epic 45.2 — Level 1 Session Memory (current conversation)."""

from __future__ import annotations

from typing import Any

from platform_memory.continuity_store import MemoryRecord, continuity_store, new_id
from platform_memory.memory_permissions import MemoryPrincipal, can_write


class ConversationMemory:
    """Session-scoped turns shared across Telegram / Web / Desktop / Voice."""

    def session_key(self, owner_id: str, session_id: str | None = None) -> str:
        return f"{owner_id}:{session_id or 'default'}"

    def append(
        self,
        principal: MemoryPrincipal,
        *,
        role: str,
        content: str,
        session_id: str | None = None,
        channel: str = "web",
        project_id: str | None = None,
    ) -> dict[str, Any]:
        if not can_write(principal):
            return {"error": "forbidden"}
        sk = self.session_key(principal.owner_id, session_id)
        rec = MemoryRecord(
            id=new_id("turn"),
            owner_id=principal.owner_id,
            company_id=principal.company_id,
            level="session",
            kind="conversation",
            title=f"{role}",
            content=content,
            channel=channel,
            project_id=project_id,
            role=principal.role,
            metadata={"session_id": session_id or "default", "turn_role": role},
        )
        continuity_store.save(rec, principal=principal)
        continuity_store.sessions.setdefault(sk, []).append(rec.id)
        return rec.to_dict()

    def history(
        self,
        principal: MemoryPrincipal,
        *,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        sk = self.session_key(principal.owner_id, session_id)
        ids = continuity_store.sessions.get(sk, [])[-limit:]
        out: list[dict[str, Any]] = []
        for mid in ids:
            r = continuity_store.get(mid, principal=principal)
            if r:
                out.append(r.to_dict())
        return out

    def clear_session(self, principal: MemoryPrincipal, session_id: str | None = None) -> int:
        sk = self.session_key(principal.owner_id, session_id)
        ids = continuity_store.sessions.pop(sk, [])
        n = 0
        for mid in ids:
            if continuity_store.remove(mid, principal=principal):
                n += 1
        return n


conversation_memory = ConversationMemory()
