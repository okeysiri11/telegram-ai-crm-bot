"""Tracking health semantics — never delete events to go green.

Classes:
  delivered
  retry_scheduled
  delivery_failed
  provider_not_configured
"""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.projects import STATUS_CONNECTED, STATUS_DEGRADED, status_payload
from services.recruiting_ops.tracking_adapters import (
    CORE_DESTINATIONS,
    PROVIDER_DESTINATIONS,
    destination_of,
    is_core_destination,
)
from services.recruiting_ops.tracking_worker import get_tracking_worker


def is_durable(item: dict[str, Any]) -> bool:
    return bool(
        item.get("durable")
        or item.get("storage") == "postgres"
        or item.get("persistence_mode") == "POSTGRES"
    )


def should_recover_to_delivered(item: dict[str, Any]) -> bool:
    dest = destination_of(item)
    if dest in PROVIDER_DESTINATIONS:
        return False
    if not is_core_destination(dest) and dest not in CORE_DESTINATIONS:
        return False
    if not is_durable(item):
        return False
    status = str(item.get("delivery_status") or "").upper()
    if item.get("recovery_reason") == "persisted_in_postgres" and status == "DELIVERED":
        return False
    return status in {"", "FAILED", "RETRYING", "PENDING"}


def classify_item(item: dict[str, Any]) -> str:
    dest = destination_of(item)
    if dest in PROVIDER_DESTINATIONS:
        return "provider_not_configured"
    status = str(item.get("delivery_status") or "").upper()
    if item.get("recovery_reason") == "persisted_in_postgres" or status == "DELIVERED":
        return "delivered"
    if is_durable(item) and is_core_destination(dest):
        return "delivered"
    if status == "RETRYING":
        return "retry_scheduled"
    if status == "FAILED":
        return "delivery_failed"
    return "retry_scheduled"


def build_tracking_diagnostics(events: list[dict[str, Any]]) -> dict[str, Any]:
    worker = get_tracking_worker().snapshot()
    delivered = retrying = failed = unconfigured = 0
    timestamps: list[str] = []
    pending_ts: list[str] = []
    for item in events:
        klass = classify_item(item)
        if klass == "delivered":
            delivered += 1
        elif klass == "retry_scheduled":
            retrying += 1
            pending_ts.append(str(item.get("created_at") or item.get("updated_at") or ""))
        elif klass == "delivery_failed":
            failed += 1
            pending_ts.append(str(item.get("created_at") or item.get("updated_at") or ""))
        elif klass == "provider_not_configured":
            unconfigured += 1
        ts = str(item.get("updated_at") or item.get("created_at") or "")
        if ts:
            timestamps.append(ts)
    retrying += int(worker.get("retrying") or 0)
    failed += int(worker.get("failed") or 0)
    oldest_pending = worker.get("oldest_pending") or (min((t for t in pending_ts if t), default=None))
    last_delivery = max((t for t in timestamps if t), default=None)
    actionable = failed > 0
    scheduled = retrying > 0
    if actionable:
        code, reason = STATUS_DEGRADED, "Есть сбои доставки в recruiting_db (delivery_failed)."
    elif scheduled:
        code, reason = STATUS_DEGRADED, "Есть события в повторной доставке (retry_scheduled)."
    else:
        code, reason = STATUS_CONNECTED, "Нет действующих сбоев доставки в ядро трекинга."
    payload = status_payload(code, reason_ru=reason)
    return {
        **payload,
        "delivered": delivered,
        "retrying": retrying,
        "failed": failed,
        "provider_not_configured": unconfigured,
        "oldest_pending": oldest_pending,
        "last_delivery": last_delivery,
        "worker": worker,
        "actionable_failures": actionable,
    }
