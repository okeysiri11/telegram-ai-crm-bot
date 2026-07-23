"""Delivery engine — tracking, retries, read receipts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.communications.models import empty_delivery_tracking
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DeliveryEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def track(
        self,
        *,
        message_id: str,
        recipient: str,
        channel: str,
        status: str = "pending",
        latency_ms: float = 0.0,
        error: str = "",
    ) -> dict[str, Any]:
        if not message_id or not recipient or not channel:
            raise ValidationError("message_id, recipient, and channel required")
        tid = _id("comm_del")
        record = empty_delivery_tracking(
            message_id=message_id,
            recipient=recipient,
            channel=channel,
            status=status,
            latency_ms=latency_ms,
            error=error,
        )
        record["delivery_id"] = tid
        record["at"] = _now()
        if status == "delivered":
            record["delivered_at"] = _now()
        return self.store.comm_deliveries.save(tid, record)

    def mark_delivered(self, *, delivery_id: str, latency_ms: float = 0.0) -> dict[str, Any]:
        rec = self.store.comm_deliveries.get(delivery_id)
        if rec is None:
            raise NotFoundError(f"delivery not found: {delivery_id}")
        rec["status"] = "delivered"
        rec["delivered_at"] = _now()
        rec["latency_ms"] = float(latency_ms)
        rec["at"] = _now()
        return self.store.comm_deliveries.save(delivery_id, rec)

    def mark_read(self, *, delivery_id: str) -> dict[str, Any]:
        rec = self.store.comm_deliveries.get(delivery_id)
        if rec is None:
            raise NotFoundError(f"delivery not found: {delivery_id}")
        rec["read_at"] = _now()
        rec["at"] = _now()
        return self.store.comm_deliveries.save(delivery_id, rec)

    def retry(self, *, delivery_id: str, error: str = "") -> dict[str, Any]:
        rec = self.store.comm_deliveries.get(delivery_id)
        if rec is None:
            raise NotFoundError(f"delivery not found: {delivery_id}")
        rec["status"] = "retry"
        rec["retries"] = int(rec.get("retries", 0)) + 1
        rec["error"] = error
        rec["at"] = _now()
        self.store.comm_deliveries.save(delivery_id, rec)
        rid = _id("comm_retry")
        return self.store.comm_retries.save(
            rid,
            {
                "retry_id": rid,
                "delivery_id": delivery_id,
                "attempt": rec["retries"],
                "error": error,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "deliveries": self.store.comm_deliveries.count(),
            "retries": self.store.comm_retries.count(),
        }
