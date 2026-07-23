"""Memory router — short/long-term, corporate, vector, documents."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_orchestrator.models import MEMORY_TIERS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MemoryRouter:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def route(
        self,
        *,
        task_id: str,
        tier: str,
        key: str,
        value: Any = None,
    ) -> dict[str, Any]:
        t = tier.lower().strip()
        if t not in MEMORY_TIERS:
            raise ValidationError(f"tier must be one of {list(MEMORY_TIERS)}")
        if not key:
            raise ValidationError("key is required")
        mid = _id("aop_mem")
        return self.store.aop_memory.save(
            mid,
            {
                "memory_id": mid,
                "task_id": task_id,
                "tier": t,
                "key": key,
                "value": value,
                "pointer": f"mem://{t}/{task_id}/{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.aop_memory.count(), "tiers": list(MEMORY_TIERS)}
