"""Epic 45.2 — Level 4 Long Term Memory (always-on preferences & facts)."""

from __future__ import annotations

from typing import Any

from platform_memory.continuity_store import MemoryRecord, continuity_store, new_id
from platform_memory.memory_permissions import MemoryPrincipal, can_write


PREFERENCE_KEYS = (
    "language",
    "favorite_models",
    "communication_style",
    "company_structure",
    "workflows",
    "timezone",
    "vertical",
)


class LongTermMemory:
    """Facts the AI should remember always for this user/company."""

    def remember(
        self,
        principal: MemoryPrincipal,
        *,
        key: str,
        value: str,
        channel: str = "web",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if not can_write(principal):
            return {"error": "forbidden"}
        existing = [
            r
            for r in continuity_store.list_for(
                principal.owner_id,
                company_id=principal.company_id,
                level="long_term",
                kind="preference",
                principal=principal,
            )
            if r.metadata.get("key") == key
        ]
        if existing:
            rec = existing[0]
            rec.content = value
            rec.title = key
            rec.channel = channel
            continuity_store.save(rec, principal=principal)
            return rec.to_dict()
        rec = MemoryRecord(
            id=new_id("ltm"),
            owner_id=principal.owner_id,
            company_id=principal.company_id,
            level="long_term",
            kind="preference",
            title=key,
            content=value,
            channel=channel,
            role=principal.role,
            tags=list(tags or ["preference"]),
            metadata={"key": key},
        )
        continuity_store.save(rec, principal=principal)
        return rec.to_dict()

    def get(self, principal: MemoryPrincipal, key: str) -> str | None:
        for r in continuity_store.list_for(
            principal.owner_id,
            company_id=principal.company_id,
            level="long_term",
            kind="preference",
            principal=principal,
        ):
            if r.metadata.get("key") == key:
                return r.content
        return None

    def all_preferences(self, principal: MemoryPrincipal) -> dict[str, str]:
        out: dict[str, str] = {}
        for r in continuity_store.list_for(
            principal.owner_id,
            company_id=principal.company_id,
            level="long_term",
            kind="preference",
            limit=200,
            principal=principal,
        ):
            k = r.metadata.get("key") or r.title
            out[str(k)] = r.content
        return out

    def profile_text(self, principal: MemoryPrincipal) -> str:
        prefs = self.all_preferences(principal)
        if not prefs:
            return "Предпочтения ещё не сохранены."
        lines = ["Долгосрочная память:"]
        for k, v in prefs.items():
            lines.append(f"• {k}: {v}")
        return "\n".join(lines)


long_term_memory = LongTermMemory()
