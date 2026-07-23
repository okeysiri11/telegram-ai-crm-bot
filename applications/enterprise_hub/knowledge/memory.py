"""AI Memory — long-term, conversation, business, project, decision, workflow memory."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIMemory:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.memory_types = list(DEFAULT_CONFIG.kg_memory_types)

    def remember(
        self,
        *,
        memory_type: str,
        subject: str,
        content: str,
        version: int = 1,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        mt = memory_type.lower().strip()
        if mt not in self.memory_types:
            raise ValidationError(f"memory_type must be one of {self.memory_types}")
        if not subject or not content:
            raise ValidationError("subject and content required")
        mid = _id("kg_mem")
        return self.store.kg_memories.save(
            mid,
            {
                "memory_id": mid,
                "memory_type": mt,
                "subject": subject,
                "content": content,
                "version": int(version),
                "tags": tags or [],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "memories": self.store.kg_memories.count(),
            "types": self.memory_types,
        }
