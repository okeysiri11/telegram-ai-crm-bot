"""WhatsApp Cloud API helpers for Recruiting — health, send, webhook, matching.

Uses existing observability, public_limits, and provider_http. No second stack.
Never puts phones, tokens, names, or message text into metric labels.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from services.observability import set_metric
from services.recruiting_ops.provider_errors import AUTH_ERROR
from services.recruiting_ops.runtime import is_production_runtime

logger = logging.getLogger(__name__)

PHONE_RE = re.compile(r"\D+")
_PHONE_ORGS: dict[str, str] = {}
_WEBHOOK_SEEN: set[str] = set()

SESSION_WINDOW = timedelta(hours=24)

CANONICAL_ENV = {
    "access_token": "WHATSAPP_ACCESS_TOKEN",
    "phone_number_id": "WHATSAPP_PHONE_NUMBER_ID",
    "business_account_id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
    "verify_token": "WHATSAPP_VERIFY_TOKEN",
    "app_secret": "WHATSAPP_APP_SECRET",
}
ACCESS_TOKEN_ALIAS = "WHATSAPP_TOKEN"
ENV_REQUIRED_FOR_LIVE = (
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_VERIFY_TOKEN",
    "WHATSAPP_APP_SECRET",
)
ENV_OPTIONAL = ("WHATSAPP_BUSINESS_ACCOUNT_ID",)

REASON_WINDOW_OPEN = "SESSION_WINDOW_OPEN"
REASON_NO_INBOUND = "TEMPLATE_REQUIRED_NO_INBOUND"
REASON_WINDOW_EXPIRED = "TEMPLATE_REQUIRED_WINDOW_EXPIRED"
ERROR_TEMPLATE_REQUIRED = "TEMPLATE_REQUIRED"
ERROR_UNKNOWN_PHONE = "UNKNOWN_PHONE_NUMBER_ID"
ERROR_MALFORMED_WEBHOOK = "MALFORMED_WEBHOOK"


def reset_whatsapp_runtime_for_tests() -> None:
    _PHONE_ORGS.clear()
    _WEBHOOK_SEEN.clear()


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def env_value(*names: str) -> str:
    for name in names:
        found = _txt(os.getenv(name))
        if found:
            return found
    return ""


def access_token_from_env() -> str:
    return env_value("WHATSAPP_ACCESS_TOKEN", ACCESS_TOKEN_ALIAS)


def env_presence() -> dict[str, bool]:
    """Boolean presence of canonical names. Never returns secret values."""
    token = bool(access_token_from_env())
    return {
        "WHATSAPP_ACCESS_TOKEN": token,
        "WHATSAPP_PHONE_NUMBER_ID": bool(env_value("WHATSAPP_PHONE_NUMBER_ID")),
        "WHATSAPP_BUSINESS_ACCOUNT_ID": bool(env_value("WHATSAPP_BUSINESS_ACCOUNT_ID")),
        "WHATSAPP_VERIFY_TOKEN": bool(env_value("WHATSAPP_VERIFY_TOKEN")),
        "WHATSAPP_APP_SECRET": bool(env_value("WHATSAPP_APP_SECRET")),
        "WHATSAPP_TOKEN_ALIAS": bool(env_value(ACCESS_TOKEN_ALIAS)) and not bool(env_value("WHATSAPP_ACCESS_TOKEN")),
    }


def env_readiness(*, store_present: dict[str, bool] | None = None) -> dict[str, Any]:
    """Startup/health env contract. Does not call Graph. Never exposes secrets."""
    present = env_presence()
    extra = store_present or {}
    token = present["WHATSAPP_ACCESS_TOKEN"] or bool(extra.get("access_token"))
    phone = present["WHATSAPP_PHONE_NUMBER_ID"] or bool(extra.get("phone_number_id"))
    verify = present["WHATSAPP_VERIFY_TOKEN"] or bool(extra.get("verify_token"))
    secret = present["WHATSAPP_APP_SECRET"] or bool(extra.get("app_secret"))
    waba = present["WHATSAPP_BUSINESS_ACCOUNT_ID"] or bool(extra.get("business_account_id"))
    flags = {
        "WHATSAPP_ACCESS_TOKEN": token,
        "WHATSAPP_PHONE_NUMBER_ID": phone,
        "WHATSAPP_VERIFY_TOKEN": verify,
        "WHATSAPP_APP_SECRET": secret,
        "WHATSAPP_BUSINESS_ACCOUNT_ID": waba,
    }
    required_ok = {
        "WHATSAPP_ACCESS_TOKEN": token,
        "WHATSAPP_PHONE_NUMBER_ID": phone,
        "WHATSAPP_VERIFY_TOKEN": verify,
        "WHATSAPP_APP_SECRET": secret,
    }
    missing = [name for name, ok in required_ok.items() if not ok]
    any_required = any(required_ok.values())
    if not any_required:
        status = "NOT_CONFIGURED"
        message_ru = "Учётные данные WhatsApp не заданы."
    elif missing:
        status = "PARTIALLY_CONFIGURED"
        message_ru = "WhatsApp настроен частично. Live-проверка недоступна."
    else:
        status = "READY_FOR_LIVE_CHECK"
        message_ru = "Учётные данные заданы. Live Graph ещё не вызывался."
    return {
        "status": status,
        "env_status": status,
        "present": flags,
        "missing": missing,
        "alias_used": bool(present["WHATSAPP_TOKEN_ALIAS"]),
        "alias_name": ACCESS_TOKEN_ALIAS if present["WHATSAPP_TOKEN_ALIAS"] else None,
        "optional_missing": [] if waba else ["WHATSAPP_BUSINESS_ACCOUNT_ID"],
        "health_sends_message": False,
        "live_verified": False,
        "message_ru": message_ru,
    }


def register_phone_org(phone_number_id: str, organization_id: str) -> None:
    key = _txt(phone_number_id)
    if key:
        _PHONE_ORGS[key] = _txt(organization_id)


def phone_org_cache() -> dict[str, str]:
    return dict(_PHONE_ORGS)


def org_for_phone_number_id(phone_number_id: str) -> str | None:
    key = _txt(phone_number_id)
    if key and key in _PHONE_ORGS:
        return _PHONE_ORGS[key]
    env_phone = env_value("WHATSAPP_PHONE_NUMBER_ID")
    if key and env_phone and key == env_phone:
        return _txt(os.getenv("VANGUARD_ORGANIZATION_ID")) or "ados"
    return None


def default_vanguard_org() -> str:
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
    elif status in {"NOT_CONFIGURED", "PARTIALLY_CONFIGURED", "READY_FOR_LIVE_CHECK"}:
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
        or env_value("WHATSAPP_APP_SECRET")
        or env_value("META_ADS_APP_SECRET")
        or env_value("META_APP_SECRET")
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
    malformed = False
    if body is not None and not isinstance(body, dict):
        malformed = True
    for entry in entries:
        if not isinstance(entry, dict):
            malformed = True
            continue
        changes = entry.get("changes") or []
        if changes and not isinstance(changes, list):
            malformed = True
            continue
        for change in changes:
            if not isinstance(change, dict):
                malformed = True
                continue
            value = change.get("value") if isinstance(change.get("value"), dict) else {}
            meta = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
            phone_number_id = _txt(meta.get("phone_number_id") or phone_number_id)
            for msg in value.get("messages") or []:
                if not isinstance(msg, dict):
                    malformed = True
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
                    malformed = True
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
    return {
        "phone_number_id": phone_number_id,
        "messages": messages,
        "statuses": statuses,
        "malformed": malformed,
        "empty": not entries and not messages and not statuses,
    }


def webhook_event_key(kind: str, provider_message_id: str) -> str:
    return f"wa-webhook:{kind}:{provider_message_id}"


def is_webhook_duplicate(key: str) -> bool:
    if not key or key.endswith(":"):
        return False
    return key in _WEBHOOK_SEEN


def seen_webhook(key: str) -> bool:
    """True if this event was already processed. Does not claim store until mark_webhook_seen."""
    if not key or key.endswith(":"):
        return False
    if key in _WEBHOOK_SEEN:
        return True
    from services.recruiting_ops.shared_store import get_store

    store = get_store()
    if getattr(store, "fail_closed", False):
        return False
    marker = f"wa:{key}"
    if hasattr(store, "has_nonce") and store.has_nonce(marker):
        _WEBHOOK_SEEN.add(key)
        return True
    return False


def mark_webhook_seen(key: str) -> None:
    if not key or key.endswith(":"):
        return
    _WEBHOOK_SEEN.add(key)
    from services.recruiting_ops.shared_store import get_store

    store = get_store()
    if getattr(store, "fail_closed", False):
        return
    store.claim_nonce(f"wa:{key}", 86400)


def match_candidate(candidates: list[dict[str, Any]], phone: str) -> dict[str, Any] | None:
    needle = normalize_phone(phone)
    if not needle:
        return None
    for item in candidates:
        if phones_match(_txt(item.get("phone")), needle):
            return item
    return None


def parse_event_time(value: Any) -> datetime | None:
    raw = _txt(value)
    if not raw:
        return None
    if raw.isdigit():
        try:
            ts = int(raw)
            if ts > 10_000_000_000:
                ts = ts / 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    try:
        text = raw.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def last_inbound_at(candidate: dict[str, Any] | None, messages: list[dict[str, Any]] | None) -> datetime | None:
    times: list[datetime] = []
    cand = candidate or {}
    for key in ("whatsapp_last_inbound_at", "last_inbound_whatsapp_at"):
        parsed = parse_event_time(cand.get(key))
        if parsed:
            times.append(parsed)
    for item in messages or []:
        direction = _txt(item.get("direction")).lower()
        if direction in {"outgoing", "outbound"}:
            continue
        if direction in {"incoming", "inbound"} or item.get("from_phone"):
            parsed = parse_event_time(item.get("timestamp") or item.get("created_at"))
            if parsed:
                times.append(parsed)
    return max(times) if times else None


def session_window(candidate: dict[str, Any] | None, messages: list[dict[str, Any]] | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    inbound = last_inbound_at(candidate, messages)
    current = now or _now_dt()
    last_out = parse_event_time((candidate or {}).get("whatsapp_last_outbound_at") or (candidate or {}).get("last_outbound_whatsapp_at"))
    if inbound is None:
        return {
            "window_open": False,
            "text_allowed": False,
            "template_required": True,
            "reason": REASON_NO_INBOUND,
            "error": ERROR_TEMPLATE_REQUIRED,
            "last_inbound_at": None,
            "last_outbound_at": last_out.isoformat() if last_out else None,
            "expires_at": None,
            "message_ru": "Нет входящего WhatsApp. Исходящее текстовое сообщение запрещено — нужен одобренный шаблон.",
        }
    expires = inbound + SESSION_WINDOW
    open_window = current <= expires
    if open_window:
        return {
            "window_open": True,
            "text_allowed": True,
            "template_required": False,
            "reason": REASON_WINDOW_OPEN,
            "error": None,
            "last_inbound_at": inbound.isoformat(),
            "last_outbound_at": last_out.isoformat() if last_out else None,
            "expires_at": expires.isoformat(),
            "message_ru": "Окно обслуживания открыто. Текстовое сообщение разрешено.",
        }
    return {
        "window_open": False,
        "text_allowed": False,
        "template_required": True,
        "reason": REASON_WINDOW_EXPIRED,
        "error": ERROR_TEMPLATE_REQUIRED,
        "last_inbound_at": inbound.isoformat(),
        "last_outbound_at": last_out.isoformat() if last_out else None,
        "expires_at": expires.isoformat(),
        "message_ru": "Окно 24 часа истекло. Исходящее текстовое сообщение запрещено — нужен одобренный шаблон.",
    }


def extract_template(body: dict[str, Any] | None) -> dict[str, Any] | None:
    payload = body if isinstance(body, dict) else {}
    nested = payload.get("template") if isinstance(payload.get("template"), dict) else {}
    name = _txt(payload.get("template_name") or nested.get("name"))
    if not name:
        return None
    lang_raw = payload.get("language") if payload.get("language") not in (None, "") else payload.get("language_code")
    if lang_raw in (None, ""):
        lang_raw = nested.get("language")
    if isinstance(lang_raw, dict):
        language = _txt(lang_raw.get("code"))
    else:
        language = _txt(lang_raw)
    language = language or "en_US"
    components = payload.get("components") if isinstance(payload.get("components"), list) else nested.get("components")
    if not isinstance(components, list):
        parameters = payload.get("parameters") if isinstance(payload.get("parameters"), list) else nested.get("parameters")
        components = _components_from_parameters(parameters)
    return {"name": name, "language": language, "components": components or []}


def _components_from_parameters(parameters: Any) -> list[dict[str, Any]]:
    if not isinstance(parameters, list) or not parameters:
        return []
    params: list[dict[str, Any]] = []
    for item in parameters:
        if isinstance(item, dict) and _txt(item.get("type")):
            params.append(item)
        else:
            params.append({"type": "text", "text": _txt(item)})
    return [{"type": "body", "parameters": params}]


def build_template_message(
    *,
    to: str,
    name: str,
    language: str = "en_US",
    components: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Cloud API template payload. Does not hard-code a production template name."""
    recipient = normalize_phone(to) or _txt(to)
    lang = _txt(language) or "en_US"
    template: dict[str, Any] = {
        "name": _txt(name),
        "language": {"code": lang},
    }
    if components:
        template["components"] = components
    return {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": template,
    }


def build_text_message(*, to: str, text: str) -> dict[str, Any]:
    return {
        "messaging_product": "whatsapp",
        "to": normalize_phone(to) or _txt(to),
        "type": "text",
        "text": {"body": _txt(text)},
    }


def outbound_idempotency_key(
    *,
    organization_id: str,
    candidate_id: str,
    to: str,
    client_key: str | None,
    body: str = "",
    template_name: str = "",
) -> str | None:
    raw = _txt(client_key)
    if raw:
        return f"wa-send:{organization_id}:{raw}"[:240]
    return None


def log_webhook_event(event: str, **fields: Any) -> None:
    safe = {key: value for key, value in fields.items() if key not in {"token", "secret", "body", "text", "signature"}}
    logger.info("whatsapp_webhook event=%s %s", event, " ".join(f"{k}={v}" for k, v in safe.items()))


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
        "message_kind": item.get("message_kind") or item.get("type") or "text",
        "template_name": item.get("template_name"),
        "window_open": item.get("window_open"),
        "template_required": item.get("template_required"),
    }
