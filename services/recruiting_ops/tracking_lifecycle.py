"""Durable tracking lifecycle. Events are never deleted to go green.

States:
  PENDING, PROCESSING, RETRYING, WAITING_PROVIDER, DELIVERED, DEAD_LETTER

FAILED is a read alias of DEAD_LETTER.
WAITING_PROVIDER is retryable when the destination provider becomes configured.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from services.recruiting_ops.projects import STATUS_CONNECTED, STATUS_DEGRADED, status_payload
from services.recruiting_ops.tracking_adapters import (
    PROVIDER_DESTINATIONS,
    TEST_DESTINATIONS,
    destination_of,
    is_core_destination,
)

PENDING = "PENDING"
PROCESSING = "PROCESSING"
RETRYING = "RETRYING"
WAITING_PROVIDER = "WAITING_PROVIDER"
DELIVERED = "DELIVERED"
DEAD_LETTER = "DEAD_LETTER"
FAILED_ALIAS = "FAILED"

MAX_ATTEMPTS = 5
STUCK_GRACE_SECONDS = 120


def backoff_base_seconds() -> float:
    return 0.0 if os.environ.get("PYTEST_CURRENT_TEST") else 2.0


BACKOFF_BASE_SECONDS = backoff_base_seconds()

CORE_MISCLASSIFIED = {PENDING, PROCESSING, RETRYING, FAILED_ALIAS, ""}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def normalize_status(raw: Any) -> str:
    status = str(raw or "").strip().upper()
    if status == FAILED_ALIAS:
        return DEAD_LETTER
    if status in {PENDING, PROCESSING, RETRYING, WAITING_PROVIDER, DELIVERED, DEAD_LETTER}:
        return status
    return PENDING if not status else status


def is_durable(item: dict[str, Any]) -> bool:
    return bool(
        item.get("durable")
        or item.get("storage") == "postgres"
        or item.get("persistence_mode") == "POSTGRES"
    )


def provider_is_configured(dest: str) -> bool:
    dest = (dest or "").strip().lower()
    if dest not in PROVIDER_DESTINATIONS:
        return False
    from services.recruiting_ops.provider_connections import is_runtime_connected

    return is_runtime_connected(dest)


def classify_lifecycle(item: dict[str, Any]) -> str:
    dest = destination_of(item)
    status = normalize_status(item.get("delivery_status"))
    if dest in PROVIDER_DESTINATIONS:
        if status == DELIVERED and item.get("delivery_class") == "provider_not_configured":
            return WAITING_PROVIDER
        if status in {WAITING_PROVIDER, PENDING, RETRYING, PROCESSING} and not provider_is_configured(dest):
            return WAITING_PROVIDER
        if status == DEAD_LETTER:
            exhausted = int(item.get("attempt") or 0) >= MAX_ATTEMPTS and bool(item.get("last_error"))
            permanent = str(item.get("dead_letter_reason") or "") in {
                "max_attempts_exceeded",
                "malformed",
                "unknown_destination",
            }
            if not provider_is_configured(dest) and not exhausted and not permanent:
                return WAITING_PROVIDER
            return DEAD_LETTER
        if provider_is_configured(dest) and status in {WAITING_PROVIDER, PENDING}:
            return RETRYING
        return status if status in {PENDING, PROCESSING, RETRYING, DELIVERED, DEAD_LETTER, WAITING_PROVIDER} else WAITING_PROVIDER
    if dest in TEST_DESTINATIONS and status == DELIVERED:
        return DELIVERED
    if status == DELIVERED or item.get("recovery_reason") == "persisted_in_postgres":
        return DELIVERED
    if is_durable(item) and is_core_destination(dest) and status in CORE_MISCLASSIFIED | {DEAD_LETTER}:
        if status == DEAD_LETTER and item.get("dead_letter_reason") and item.get("dead_letter_reason") not in {
            "persisted_in_postgres_misclassified",
            "",
        }:
            if int(item.get("attempt") or 0) >= MAX_ATTEMPTS and item.get("last_error"):
                return DEAD_LETTER
        if is_durable(item) and is_core_destination(dest) and not item.get("last_error"):
            return DELIVERED
    if status == DEAD_LETTER:
        return DEAD_LETTER
    if status == RETRYING:
        return RETRYING
    if status == PROCESSING:
        return PROCESSING
    if status == PENDING:
        return PENDING
    if is_durable(item) and is_core_destination(dest):
        return DELIVERED
    return RETRYING if status == RETRYING else PENDING


def should_recover_to_delivered(item: dict[str, Any]) -> bool:
    dest = destination_of(item)
    if dest in PROVIDER_DESTINATIONS:
        return False
    if not is_core_destination(dest):
        return False
    if not is_durable(item):
        return False
    status = normalize_status(item.get("delivery_status"))
    if status == DELIVERED and item.get("recovery_reason") == "persisted_in_postgres":
        return False
    if status == DELIVERED:
        return False
    if status == DEAD_LETTER and item.get("last_error") and int(item.get("attempt") or 0) >= MAX_ATTEMPTS:
        return False
    return True


def backoff_seconds(attempt: int) -> float:
    n = max(1, int(attempt or 1))
    return backoff_base_seconds() * (2 ** (n - 1))


def next_attempt_at(attempt: int, *, now: datetime | None = None) -> str:
    stamp = now or utc_now()
    return (stamp + timedelta(seconds=backoff_seconds(attempt))).isoformat()


def is_due(item: dict[str, Any], *, now: datetime | None = None) -> bool:
    raw = item.get("next_attempt_at")
    if not raw:
        return True
    try:
        due = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return True
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return due <= (now or utc_now())


def is_stuck_retry(item: dict[str, Any], *, now: datetime | None = None) -> bool:
    if classify_lifecycle(item) != RETRYING:
        return False
    stamp = now or utc_now()
    raw = item.get("next_attempt_at") or item.get("last_attempt_at") or item.get("updated_at")
    if not raw:
        return int(item.get("attempt") or 0) >= 1
    try:
        ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (stamp - ts).total_seconds() > STUCK_GRACE_SECONDS and is_due(item, now=stamp)


def migration_patch(item: dict[str, Any]) -> dict[str, Any] | None:
    """Return payload patch for a historical row. Never deletes."""
    dest = destination_of(item)
    status = normalize_status(item.get("delivery_status"))
    durable = is_durable(item)
    if dest in PROVIDER_DESTINATIONS:
        if provider_is_configured(dest):
            if status == WAITING_PROVIDER:
                return {
                    "delivery_status": RETRYING,
                    "delivery_class": "retry_scheduled",
                    "next_attempt_at": iso_now(),
                    "destination": dest,
                }
            return None
        if status != WAITING_PROVIDER:
            return {
                "delivery_status": WAITING_PROVIDER,
                "delivery_class": "waiting_provider",
                "provider_status": "NOT_CONFIGURED",
                "destination": dest,
                "message_ru": f"Провайдер {dest} не настроен; событие сохранено и будет повторено после настройки.",
            }
        return None
    if not durable:
        return None
    if dest in TEST_DESTINATIONS:
        if status != DELIVERED:
            return {"delivery_status": DELIVERED, "delivery_class": "delivered", "adapter": "test"}
        return None
    if not is_core_destination(dest):
        return {
            "delivery_status": DEAD_LETTER,
            "delivery_class": "dead_letter",
            "dead_letter_reason": "unknown_destination",
            "last_error": f"unknown_destination:{dest}",
            "message_ru": "Неизвестное направление доставки.",
        }
    if status == DELIVERED:
        if not item.get("durable"):
            return {"durable": True, "storage": "postgres", "persistence_mode": "POSTGRES"}
        return None
    if status == DEAD_LETTER and item.get("last_error") and int(item.get("attempt") or 0) >= MAX_ATTEMPTS:
        return None
    return {
        "delivery_status": DELIVERED,
        "delivery_class": "delivered",
        "durable": True,
        "storage": item.get("storage") or "postgres",
        "persistence_mode": "POSTGRES",
        "recovery_reason": "persisted_in_postgres",
        "destination": dest or "recruiting_db",
        "message_ru": "Событие уже записано в recruiting_db (PostgreSQL).",
    }


def classify_item(item: dict[str, Any]) -> str:
    """Health class used by counters."""
    life = classify_lifecycle(item)
    if life == DELIVERED:
        return "delivered"
    if life == WAITING_PROVIDER:
        return "waiting_provider"
    if life == DEAD_LETTER:
        return "dead_letter"
    if life == PROCESSING:
        return "processing"
    if life == RETRYING:
        return "retry_scheduled"
    return "pending"


def build_tracking_diagnostics(events: list[dict[str, Any]], worker: dict[str, Any] | None = None) -> dict[str, Any]:
    from services.recruiting_ops.tracking_worker import get_tracking_worker

    snap = worker if worker is not None else get_tracking_worker().snapshot()
    pending = processing = retrying = waiting = delivered = dead = 0
    timestamps: list[str] = []
    pending_ts: list[str] = []
    stuck = 0
    for item in events:
        klass = classify_item(item)
        if klass == "delivered":
            delivered += 1
        elif klass == "waiting_provider":
            waiting += 1
        elif klass == "dead_letter":
            dead += 1
        elif klass == "processing":
            processing += 1
            pending_ts.append(str(item.get("created_at") or item.get("updated_at") or ""))
        elif klass == "retry_scheduled":
            retrying += 1
            pending_ts.append(str(item.get("created_at") or item.get("updated_at") or ""))
            if is_stuck_retry(item):
                stuck += 1
        else:
            pending += 1
            pending_ts.append(str(item.get("created_at") or item.get("updated_at") or ""))
        ts = str(item.get("updated_at") or item.get("created_at") or "")
        if ts:
            timestamps.append(ts)
    retrying = max(retrying, int(snap.get("retrying") or 0))
    storm = stuck > 0
    infra_fail = stuck > 0
    worker_down = snap.get("enabled") is False
    if worker_down:
        code, reason = STATUS_DEGRADED, "Воркер трекинга остановлен."
    elif infra_fail:
        code, reason = STATUS_DEGRADED, "Есть застрявшие повторные доставки в ядро трекинга."
    elif storm:
        code, reason = STATUS_DEGRADED, "Неконтролируемый поток повторов трекинга."
    else:
        code, reason = STATUS_CONNECTED, "Инфраструктура трекинга работает. Ожидание провайдеров не считается сбоем."
    payload = status_payload(code, reason_ru=reason)
    return {
        **payload,
        "pending": pending,
        "processing": processing,
        "retrying": retrying,
        "waiting_provider": waiting,
        "delivered": delivered,
        "dead_letter": dead,
        "failed": dead,
        "provider_not_configured": waiting,
        "oldest_pending": snap.get("oldest_pending") or (min((t for t in pending_ts if t), default=None)),
        "last_delivery": max((t for t in timestamps if t), default=None),
        "worker": snap,
        "actionable_failures": infra_fail,
        "retry_storm": bool(storm),
    }
