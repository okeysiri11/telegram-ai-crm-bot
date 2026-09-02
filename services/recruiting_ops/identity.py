"""Candidate identity matching — never collapses leads; never merges ambiguous people."""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.whatsapp_ops import normalize_phone, phones_match

APPLICATION_SNAPSHOT_KEYS = (
    "name",
    "email",
    "phone",
    "source",
    "campaign_id",
    "vacancy_id",
    "vacancy",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "first_touch_source",
    "first_touch_medium",
    "first_touch_campaign",
    "last_touch_source",
    "last_touch_medium",
    "last_touch_campaign",
    "external_id",
    "idempotency_key",
    "submitted_at",
    "created_at",
    "program_of_interest",
    "unit_of_interest",
    "application_message",
    "gclid",
    "fbclid",
    "click_id",
    "referrer",
    "landing_page",
    "project_key",
)


def _txt(value: Any) -> str:
    return str(value or "").strip()


def normalize_email(value: Any) -> str:
    return _txt(value).lower()


def identity_lock_key(organization_id: str, email: Any, phone: Any) -> str:
    mail = normalize_email(email)
    phone_n = normalize_phone(_txt(phone))
    return f"{organization_id}:{mail}:{phone_n}"


def identity_decision(left: dict[str, Any], right: dict[str, Any]) -> str:
    """Return match | ambiguous | distinct. Name is never an identity key."""
    email_a, email_b = normalize_email(left.get("email")), normalize_email(right.get("email"))
    phone_a_n = normalize_phone(_txt(left.get("phone")))
    phone_b_n = normalize_phone(_txt(right.get("phone")))
    email_same = bool(email_a and email_b and email_a == email_b)
    phone_same = bool(phone_a_n and phone_b_n and phones_match(_txt(left.get("phone")), _txt(right.get("phone"))))
    if email_same and phone_same:
        return "match"
    if email_same and not phone_a_n and not phone_b_n:
        return "match"
    if phone_same and not email_a and not email_b:
        return "match"
    if email_same or phone_same:
        return "ambiguous"
    return "distinct"


def application_snapshot(lead: dict[str, Any]) -> dict[str, Any]:
    snap: dict[str, Any] = {"lead_id": _txt(lead.get("id"))}
    for key in APPLICATION_SNAPSHOT_KEYS:
        if key in lead and lead.get(key) not in (None, ""):
            snap[key] = lead.get(key)
    return snap


def linked_lead_ids(candidate: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for raw in list(candidate.get("lead_ids") or []) + [_txt(candidate.get("lead_id"))]:
        lid = _txt(raw)
        if not lid or lid in seen:
            continue
        seen.add(lid)
        ids.append(lid)
    for app in candidate.get("applications") or []:
        lid = _txt(app.get("lead_id") if isinstance(app, dict) else "")
        if lid and lid not in seen:
            seen.add(lid)
            ids.append(lid)
    return ids
