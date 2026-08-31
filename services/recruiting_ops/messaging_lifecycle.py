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
    nested = body.get("template") if isinstance(body.get("template"), dict) else {}
    template_name = _txt(body.get("template_name") or nested.get("name"))
    if not text and not template_name:
        return {"ok": False, "error": "validation", "message_ru": "Укажите текст сообщения или шаблон."}
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
            "template_name": template_name or None,
            "template": body.get("template") if isinstance(body.get("template"), dict) else None,
            "language": _txt(body.get("language") or body.get("language_code")) or None,
            "components": body.get("components") if isinstance(body.get("components"), list) else None,
            "parameters": body.get("parameters") if isinstance(body.get("parameters"), list) else None,
            "message_kind": "template" if template_name else "text",
            "status": status,
            "approval_required": True,
            "sent": False,
            "journal_only": not connected,
            "provider_message_id": None,
            "created_at": _now(),
        },
    }
