"""In-app signal notification lifecycle — no Telegram/email required."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

NOTIF_STATUSES = {"ACTIVE", "TRIGGERED", "ACKNOWLEDGED", "EXPIRED", "DISABLED"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_notification(
    *,
    tenant_id: str,
    signal_id: str,
    title: str,
    body: str = "",
    instrument: str = "EUR/USD",
    status: str = "ACTIVE",
) -> dict[str, Any]:
    st = status if status in NOTIF_STATUSES else "ACTIVE"
    return {
        "notification_id": f"nt_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id or "default",
        "signal_id": signal_id,
        "instrument": instrument,
        "title": title,
        "body": body,
        "status": st,
        "status_ru": {
            "ACTIVE": "Активно",
            "TRIGGERED": "Сработало",
            "ACKNOWLEDGED": "Подтверждено",
            "EXPIRED": "Истекло",
            "DISABLED": "Отключено",
        }.get(st, st),
        "created_at": _now(),
        "updated_at": _now(),
        "actions": ["Подтвердить", "Открыть", "Отключить"],
        "channel": "in_app",
        "sound": True,
    }


def transition(notif: dict[str, Any], action: str) -> dict[str, Any]:
    a = (action or "").lower()
    out = dict(notif)
    if a in {"ack", "acknowledge", "подтвердить"}:
        out["status"] = "ACKNOWLEDGED"
    elif a in {"disable", "off", "отключить"}:
        out["status"] = "DISABLED"
    elif a in {"trigger", "triggered"}:
        out["status"] = "TRIGGERED"
    elif a in {"expire", "expired"}:
        out["status"] = "EXPIRED"
    else:
        return notif
    out["status_ru"] = {
        "ACTIVE": "Активно",
        "TRIGGERED": "Сработало",
        "ACKNOWLEDGED": "Подтверждено",
        "EXPIRED": "Истекло",
        "DISABLED": "Отключено",
    }.get(out["status"], out["status"])
    out["updated_at"] = _now()
    return out
