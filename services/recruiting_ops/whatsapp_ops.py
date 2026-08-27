"""WhatsApp Cloud API helpers for Recruiting — health, send, webhook, matching.

Uses existing observability, public_limits, and provider_http. No second stack.
Never puts phones, tokens, names, or message text into metric labels.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from datetime import datetime, timezone
from typing import Any

from services.observability import set_metric
from services.recruiting_ops.provider_errors import AUTH_ERROR
from services.recruiting_ops.runtime import is_production_runtime

PHONE_RE = re.compile(r"\D+")
_PHONE_ORGS: dict[str, str] = {}
_WEBHOOK_SEEN: set[str] = set()


def reset_whatsapp_runtime_for_tests() -> None:
    _PHONE_ORGS.clear()
    _WEBHOOK_SEEN.clear()


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_phone_org(phone_number_id: str, organization_id: str) -> None:
    key = _txt(phone_number_id)
    if key:
        _PHONE_ORGS[key] = _txt(organization_id)


def org_for_phone_number_id(phone_number_id: str) -> str:
    key = _txt(phone_number_id)
    if key and key in _PHONE_ORGS:
        return _PHONE_ORGS[key]
    return _txt(os.getenv("VANGUARD_ORGANIZATION_ID")) or "ados"


def normalize_phone(value: str) -> str:
    digits = PHONE_RE.sub("", _txt(value))
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return digits


def phones_match(left: str, right: str) -> bool:
    a, b = normalize_phone(left), normalize_phone(right)
    if not a or not b:
        return False
    if a == b:
        return True
    tail = min(len(a), len(b), 10)
    return tail >= 8 and a[-tail:] == b[-tail:]


def record_health_metric(status: str, latency_ms: int | None = None) -> None:
    if status == "CONNECTED":
        set_metric("whatsapp_provider_health", 1)
    elif status == "NOT_CONFIGURED":
        set_metric("whatsapp_provider_health", 0)
    else:
        set_metric("whatsapp_provider_health", -1)
    if latency_ms is not None:
        set_metric("whatsapp_send_latency", float(latency_ms))


def webhook_app_secret() -> str:
    from services.recruiting_ops.secret_store import get_secret_store

    store = get_secret_store()
    return (
        _txt(store.get("whatsapp", "app_secret"))
        or _txt(os.getenv("WHATSAPP_APP_SECRET"))
        or _txt(os.getenv("META_ADS_APP_SECRET"))
        or _txt(os.getenv("META_APP_SECRET"))
    )


def verify_webhook_signature(raw: bytes | None, signature: str | None) -> dict[str, Any]:
    sig = _txt(signature)
    secret = webhook_app_secret()
    if not sig:
        if is_production_runtime() and secret and not os.environ.get("PYTEST_CURRENT_TEST"):
            return {"ok": False, "error": AUTH_ERROR, "message_ru": "Подпись webhook отсутствует."}
        return {"ok": True, "verified": False, "optional": True}
    if not secret:
        return {"ok": False, "error": AUTH_ERROR, "message_ru": "Секрет подписи webhook не задан."}
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), raw or b"", hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return {"ok": False, "error": AUTH_ERROR, "message_ru": "Подпись webhook недействительна."}
    return {"ok": True, "verified": True}


def safe_provider_error(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    errors = payload.get("errors") if isinstance(payload.get("errors"), list) else []
    first = errors[0] if errors and isinstance(errors[0], dict) else {}
    title = _txt(first.get("title") or first.get("message") or payload.get("title"))
    code = first.get("code") or payload.get("code")
    if not title and code is None:
        return None
    lowered = title.lower()
    if any(part in lowered for part in ("token", "secret", "bearer", "password")):
        title = "Ошибка провайдера"
    return {"code": code, "title": title[:160] if title else None}


def parse_webhook(body: dict[str, Any] | None) -> dict[str, Any]:
    payload = body if isinstance(body, dict) else {}
    entries = payload.get("entry") if isinstance(payload.get("entry"), list) else []
    messages: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []
    phone_number_id = ""
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            if not isinstance(change, dict):
                continue
            value = change.get("value") if isinstance(change.get("value"), dict) else {}
            meta = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
            phone_number_id = _txt(meta.get("phone_number_id") or phone_number_id)
            for msg in value.get("messages") or []:
                if not isinstance(msg, dict):
                    continue
                text_obj = msg.get("text") if isinstance(msg.get("text"), dict) else {}
                messages.append(
                    {
                        "provider_message_id": _txt(msg.get("id")),
                        "from": _txt(msg.get("from")),
                        "timestamp": _txt(msg.get("timestamp")),
                        "type": _txt(msg.get("type") or "text"),
                        "body": _txt(text_obj.get("body") or msg.get("body")),
                    }
                )
            for status in value.get("statuses") or []:
                if not isinstance(status, dict):
                    continue
                statuses.append(
                    {
                        "provider_message_id": _txt(status.get("id")),
                        "status": _txt(status.get("status")).lower(),
                        "timestamp": _txt(status.get("timestamp")),
                        "recipient": _txt(status.get("recipient_id")),
                        "error": safe_provider_error(status),
                    }
                )
    return {"phone_number_id": phone_number_id, "messages": messages, "statuses": statuses}


def webhook_event_key(kind: str, provider_message_id: str) -> str:
    return f"wa-webhook:{kind}:{provider_message_id}"


def seen_webhook(key: str) -> bool:
    if not key or key.endswith(":"):
        return False
    if key in _WEBHOOK_SEEN:
        return True
    from services.recruiting_ops.shared_store import get_store

    store = get_store()
    if getattr(store, "fail_closed", False):
        _WEBHOOK_SEEN.add(key)
        return False
    claimed = store.claim_nonce(f"wa:{key}", 86400)
    _WEBHOOK_SEEN.add(key)
    return not claimed


def mark_webhook_seen(key: str) -> None:
    if key:
        _WEBHOOK_SEEN.add(key)


def match_candidate(candidates: list[dict[str, Any]], phone: str) -> dict[str, Any] | None:
    needle = normalize_phone(phone)
    if not needle:
        return None
    for item in candidates:
        if phones_match(_txt(item.get("phone")), needle):
            return item
    return None


def ai_draft(*, name: str = "", vacancy: str = "") -> dict[str, Any]:
    person = _txt(name) or "кандидат"
    role = _txt(vacancy)
    text = f"Здравствуйте, {person}."
    if role:
        text += f" Пишем по вакансии {role}."
    text += " Подскажите, удобно ли продолжить переписку в WhatsApp?"
    return {
        "ok": True,
        "body": text,
        "advisory_only": True,
        "live_write_access": False,
        "sent": False,
        "provider": "whatsapp",
        "message_ru": "Черновик AI. Отправка только после подтверждения человеком.",
    }


def public_conversation_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "provider": "whatsapp",
        "channel": "WHATSAPP",
        "direction": item.get("direction"),
        "to": item.get("to"),
        "from_phone": item.get("from_phone"),
        "body": item.get("body"),
        "created_at": item.get("created_at") or item.get("timestamp"),
        "send_status": item.get("send_status") or item.get("status"),
        "delivered": bool(item.get("delivered") or item.get("status") == "DELIVERED"),
        "read": bool(item.get("read")),
        "failed": bool(item.get("failed") or item.get("status") == "FAILED"),
        "status": item.get("status"),
        "provider_error": item.get("provider_error"),
        "candidate_id": item.get("candidate_id"),
        "unresolved": bool(item.get("unresolved")),
        "approval_required": bool(item.get("approval_required")),
        "sent": bool(item.get("sent")),
        "delivered_status": bool(item.get("delivered")),
        "read_status": bool(item.get("read")),
        "failed_status": bool(item.get("failed")),
        "provider_message_id": item.get("provider_message_id"),
    }
