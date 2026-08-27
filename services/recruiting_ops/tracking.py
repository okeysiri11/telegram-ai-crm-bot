"""Vanguard tracking contract — no passwords, no device fingerprinting."""

from __future__ import annotations

from typing import Any

EVENT_TYPES = (
    "page_view",
    "application_open",
    "application_start",
    "application_submit",
    "application_success",
)

FORBIDDEN_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "cookie",
    "authorization",
    "canvas",
    "webrtc",
    "fingerprint",
    "user_agent",
    "ua",
    "ip",
    "ip_address",
}


def _txt(value: Any) -> str:
    return str(value or "").strip()


def sanitize_tracking_body(body: dict[str, Any]) -> dict[str, Any]:
    cleaned = {k: v for k, v in body.items() if str(k).lower() not in FORBIDDEN_KEYS}
    event_type = _txt(cleaned.get("event_type")).lower()
    return {
        "visitor_id": _txt(cleaned.get("visitor_id")) or None,
        "session_id": _txt(cleaned.get("session_id")) or None,
        "event_id": _txt(cleaned.get("event_id")) or None,
        "event_type": event_type if event_type in EVENT_TYPES else "",
        "timestamp": _txt(cleaned.get("timestamp")) or None,
        "page": _txt(cleaned.get("page")) or None,
        "referrer": _txt(cleaned.get("referrer")) or None,
        "landing_page": _txt(cleaned.get("landing_page") or cleaned.get("page")) or None,
        "utm_source": _txt(cleaned.get("utm_source")) or None,
        "utm_medium": _txt(cleaned.get("utm_medium")) or None,
        "utm_campaign": _txt(cleaned.get("utm_campaign")) or None,
        "utm_content": _txt(cleaned.get("utm_content")) or None,
        "utm_term": _txt(cleaned.get("utm_term")) or None,
        "campaign_id": _txt(cleaned.get("campaign_id")) or None,
        "project_key": "vanguard",
        "source": "vanguard",
    }


def validate_tracking(event: dict[str, Any]) -> str | None:
    if event.get("event_type") not in EVENT_TYPES:
        return "Некорректный event_type"
    return None
