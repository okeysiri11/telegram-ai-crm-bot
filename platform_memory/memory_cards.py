"""Epic 45.2 — Memory Cards for platform objects."""

from __future__ import annotations

from typing import Any

from platform_memory.continuity_store import MemoryRecord, continuity_store, new_id
from platform_memory.memory_embeddings import memory_embeddings
from platform_memory.memory_permissions import MemoryPrincipal, can_write

CARD_KINDS = (
    "client",
    "project",
    "document",
    "deal",
    "video",
    "image",
    "chat",
    "ai_agent",
    "workflow",
    "vertical",
)


class MemoryCards:
    def attach(
        self,
        principal: MemoryPrincipal,
        *,
        object_kind: str,
        object_id: str,
        title: str,
        content: str = "",
        channel: str = "web",
        project_id: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if object_kind not in CARD_KINDS:
            return {"error": "unknown_card_kind", "allowed": list(CARD_KINDS)}
        if not can_write(principal):
            return {"error": "forbidden"}
        existing = [
            r
            for r in continuity_store.list_for(
                principal.owner_id, kind="card", limit=500, principal=principal
            )
            if r.metadata.get("object_id") == object_id and r.metadata.get("object_kind") == object_kind
        ]
        text = content or title
        emb = memory_embeddings.embed(f"{title} {text}")
        if existing:
            rec = existing[0]
            rec.title = title
            rec.content = text
            rec.embedding = emb
            rec.channel = channel
            continuity_store.save(rec, principal=principal)
            return rec.to_dict()
        rec = MemoryRecord(
            id=new_id("card"),
            owner_id=principal.owner_id,
            company_id=principal.company_id,
            level="knowledge",
            kind="card",
            title=title,
            content=text,
            channel=channel,
            project_id=project_id,
            role=principal.role,
            tags=list(tags or [object_kind]),
            embedding=emb,
            metadata={"object_kind": object_kind, "object_id": object_id},
        )
        continuity_store.save(rec, principal=principal)
        return rec.to_dict()

    def for_object(self, principal: MemoryPrincipal, object_kind: str, object_id: str) -> dict[str, Any] | None:
        for r in continuity_store.list_for(principal.owner_id, kind="card", limit=500, principal=principal):
            if r.metadata.get("object_kind") == object_kind and r.metadata.get("object_id") == object_id:
                if r.company_id == principal.company_id:
                    return r.to_dict()
        return None

    def list_cards(self, principal: MemoryPrincipal, *, object_kind: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        out = []
        for r in continuity_store.list_for(
            principal.owner_id, company_id=principal.company_id, kind="card", limit=limit, principal=principal
        ):
            if object_kind and r.metadata.get("object_kind") != object_kind:
                continue
            out.append(r.to_dict())
        return out


memory_cards = MemoryCards()
