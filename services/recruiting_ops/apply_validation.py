"""Server-side validation for public Vanguard applications."""

from __future__ import annotations

import os
import re
from typing import Any

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_FIELD = 500
_MAX_MESSAGE = 4000


def max_body_bytes() -> int:
    raw = (os.getenv("VANGUARD_APPLY_MAX_BYTES") or "").strip()
    try:
        return max(64, int(raw)) if raw else 32768
    except ValueError:
        return 32768


def apply_timeout_seconds() -> float:
    raw = (os.getenv("VANGUARD_APPLY_TIMEOUT_SECONDS") or "").strip()
    try:
        return max(1.0, float(raw)) if raw else 15.0
    except ValueError:
        return 15.0


def _txt(value: Any, *, limit: int = _MAX_FIELD) -> str:
    return str(value or "").strip()[:limit]


def normalize_email(value: Any) -> str:
    return _txt(value).lower()


def validate_application_body(body: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {"ok": False, "error": "validation", "message_ru": "Некорректное тело запроса"}
    first = _txt(body.get("first_name"))
    last = _txt(body.get("last_name"))
    name = _txt(body.get("name") or body.get("full_name") or " ".join(p for p in (first, last) if p))
    email = normalize_email(body.get("email"))
    if not name:
        return {"ok": False, "error": "validation", "message_ru": "Укажите имя"}
    if not email or not _EMAIL_RE.match(email):
        return {"ok": False, "error": "validation", "message_ru": "Укажите корректный email"}
    cleaned = dict(body)
    cleaned["first_name"] = first
    cleaned["last_name"] = last
    cleaned["name"] = name
    cleaned["email"] = email
    cleaned["country"] = _txt(body.get("country"))
    cleaned["preferred_language"] = _txt(body.get("preferred_language") or body.get("language") or "ru")
    cleaned["unit_of_interest"] = _txt(body.get("unit_of_interest") or body.get("unit"))
    cleaned["program_of_interest"] = _txt(body.get("program_of_interest") or body.get("program"))
    cleaned["application_message"] = _txt(
        body.get("application_message") or body.get("message") or body.get("reason"),
        limit=_MAX_MESSAGE,
    )
    cleaned["idempotency_key"] = _txt(body.get("idempotency_key") or body.get("event_id"), limit=128)
    return {"ok": True, "body": cleaned}
