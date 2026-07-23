"""Notification queue — FIFO, priority, batch, rate limiting."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.communications.models import QUEUE_STATUSES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class NotificationQueue:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self._rate_window: list[str] = []
        self.rate_limit_per_batch = 100

    def enqueue(
        self,
        *,
        event_id: str,
        recipient: str,
        channel: str,
        priority: str = "medium",
        mode: str = "fifo",
    ) -> dict[str, Any]:
        if not event_id or not recipient or not channel:
            raise ValidationError("event_id, recipient, and channel required")
        mode_n = (mode or "fifo").lower().strip()
        if mode_n not in ("fifo", "priority", "batch"):
            raise ValidationError("mode must be fifo, priority, or batch")
        qid = _id("comm_q")
        weight = {"critical": 0, "high": 1, "medium": 2, "low": 3, "silent": 4}.get(
            priority.lower(), 2
        )
        return self.store.comm_queue.save(
            qid,
            {
                "queue_id": qid,
                "event_id": event_id,
                "recipient": recipient,
                "channel": channel,
                "priority": priority.lower(),
                "weight": weight,
                "mode": mode_n,
                "status": "pending",
                "at": _now(),
            },
        )

    def set_status(self, *, queue_id: str, status: str) -> dict[str, Any]:
        item = self.store.comm_queue.get(queue_id)
        if item is None:
            raise NotFoundError(f"queue item not found: {queue_id}")
        st = status.lower().strip()
        if st not in QUEUE_STATUSES:
            raise ValidationError(f"status must be one of {list(QUEUE_STATUSES)}")
        item["status"] = st
        item["at"] = _now()
        return self.store.comm_queue.save(queue_id, item)

    def dequeue_batch(self, *, limit: int = 10) -> list[dict[str, Any]]:
        pending = [
            i
            for i in self.store.comm_queue.list_all()
            if isinstance(i, dict) and i.get("status") == "pending"
        ]
        pending.sort(key=lambda x: (x.get("weight", 2), x.get("at", "")))
        batch = pending[: max(1, min(limit, self.rate_limit_per_batch))]
        for item in batch:
            item["status"] = "processing"
            item["at"] = _now()
            self.store.comm_queue.save(item["queue_id"], item)
            self._rate_window.append(item["queue_id"])
        return batch

    def rate_limit_ok(self) -> bool:
        return len(self._rate_window) < self.rate_limit_per_batch

    def status(self) -> dict[str, Any]:
        by_status: dict[str, int] = {s: 0 for s in QUEUE_STATUSES}
        for item in self.store.comm_queue.list_all():
            if isinstance(item, dict):
                st = item.get("status", "pending")
                by_status[st] = by_status.get(st, 0) + 1
        return {
            "queued": self.store.comm_queue.count(),
            "by_status": by_status,
            "rate_limit_ok": self.rate_limit_ok(),
        }
