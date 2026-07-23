"""Memory manager — short/long/project/org/personal/AI shared memory."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.knowledge_platform.models import MEMORY_TIERS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MemoryManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def store_memory(
        self,
        *,
        tier: str,
        key: str,
        value: Any,
        owner: str = "platform",
        scope: str | None = None,
    ) -> dict[str, Any]:
        t = tier.lower().strip()
        if t not in MEMORY_TIERS:
            raise ValidationError(f"tier must be one of {list(MEMORY_TIERS)}")
        if not key:
            raise ValidationError("key is required")
        mid = _id("ekp_mem")
        return self.store.ekp_memory.save(
            mid,
            {
                "memory_id": mid,
                "tier": t,
                "key": key,
                "value": value,
                "owner": owner,
                "scope": scope,
                "at": _now(),
            },
        )

    def recall(self, *, tier: str | None = None, key: str | None = None) -> list[dict[str, Any]]:
        out = []
        for m in self.store.ekp_memory.list_all():
            if tier and m.get("tier") != tier:
                continue
            if key and m.get("key") != key:
                continue
            out.append(m)
        return out

    def build_context(self, *, tiers: list[str] | None = None) -> dict[str, Any]:
        wanted = tiers or list(MEMORY_TIERS)
        items = [m for m in self.store.ekp_memory.list_all() if m.get("tier") in wanted]
        cid = _id("ekp_ctx")
        return self.store.ekp_contexts.save(
            cid,
            {
                "context_id": cid,
                "tiers": wanted,
                "items": items,
                "summary": {t: sum(1 for i in items if i.get("tier") == t) for t in wanted},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.ekp_memory.count(), "tiers": list(MEMORY_TIERS)}
