"""Retry manager — redelivery attempts with backoff metadata."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RetryManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def schedule(self, *, event_id: str, attempt: int, reason: str = "failure") -> dict[str, Any]:
        rid = _id("evp_rty")
        return self.store.evp_retries.save(
            rid,
            {
                "retry_id": rid,
                "event_id": event_id,
                "attempt": int(attempt),
                "reason": reason,
                "backoff_ms": min(1000 * (2 ** max(0, attempt - 1)), 30000),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"retries": self.store.evp_retries.count()}
