"""Memory Management — global/shared/semantic/long-term/session/vector/knowledge cache (Sprint 12.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ai_os.config import DEFAULT_CONFIG
from applications.ai_os.shared.exceptions import NotFoundError, ValidationError
from applications.ai_os.shared.store import AIOSStore, ai_os_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryManager:
    def __init__(self, store: AIOSStore | None = None) -> None:
        self.store = store or ai_os_store
        self.tiers = list(DEFAULT_CONFIG.memory_tiers)

    def put(self, *, tier: str, key: str, value: Any, ttl_s: int | None = None) -> dict[str, Any]:
        if tier not in self.tiers:
            raise ValidationError(f"tier must be one of {self.tiers}")
        if not key:
            raise ValidationError("key required")
        mid = f"mem_{tier}_{key}"
        row = {
            "memory_id": mid,
            "tier": tier,
            "key": key,
            "value": value,
            "ttl_s": ttl_s,
            "at": _now(),
        }
        self.store.memory.save(mid, row)
        return row

    def get(self, *, tier: str, key: str) -> dict[str, Any]:
        mid = f"mem_{tier}_{key}"
        item = self.store.memory.get(mid)
        if item is None:
            raise NotFoundError("memory", mid)
        return item

    def list_tier(self, tier: str) -> list[dict[str, Any]]:
        return [m for m in self.store.memory.list_all() if m.get("tier") == tier]

    def clear_tier(self, tier: str) -> dict[str, Any]:
        removed = 0
        for item in list(self.list_tier(tier)):
            self.store.memory.delete(item["memory_id"])
            removed += 1
        return {"tier": tier, "removed": removed}

    def status(self) -> dict[str, Any]:
        return {
            "memory_management": "1.0",
            "tiers": self.tiers,
            "entries": len(self.store.memory.list_all()),
            "ready": True,
        }


memory_manager = MemoryManager()
