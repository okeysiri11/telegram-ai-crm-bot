"""Recruiting outbound messaging lifecycle. Unconfigured providers stay WAITING_PROVIDER."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

DRAFT = "DRAFT"
APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
APPROVED = "APPROVED"
QUEUED = "QUEUED"
SENDING = "SENDING"
SENT = "SENT"
DELIVERED = "DELIVERED"
FAILED = "FAILED"
WAITING_PROVIDER = "WAITING_PROVIDER"

MESSAGE_STATES = (DRAFT, APPROVAL_REQUIRED, APPROVED, QUEUED, SENDING, SENT, DELIVERED, FAILED, WAITING_PROVIDER)
CHANNELS = ("telegram", "whatsapp", "email")


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_outbound(body: dict[str, Any], *, connected: bool) -> dict[str, Any]:
    channel = _txt(body.get("channel") or body.get("provider")).lower()
    if channel not in CHANNELS:
        return {"ok": False, "error": "validation", "message_ru": "Канал должен быть telegram, whatsapp или email."}
    text = _txt(body.get("body") or body.get("text") or body.get("message"))
    if not text:
        return {"ok": False, "error": "validation", "message_ru": "Укажите текст сообщения."}
    if not connected:
        status = WAITING_PROVIDER
    else:
        status = APPROVAL_REQUIRED
    return {
        "ok": True,
        "item": {
            "channel": channel,
            "provider": channel,
            "to": _txt(body.get("to") or body.get("chat_id") or body.get("phone") or body.get("email")) or None,
            "body": text,
            "status": status,
            "approval_required": True,
            "sent": False,
            "journal_only": not connected,
            "provider_message_id": None,
            "created_at": _now(),
        },
    }
