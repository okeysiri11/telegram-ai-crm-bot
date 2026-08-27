"""Unified provider lead ingestion — normalize + deduplicate without rewriting history."""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.attribution import preserve_first_touch, touch_payload


def _txt(value: Any) -> str:
    return str(value or "").strip()


def normalize_provider_lead(body: dict[str, Any]) -> dict[str, Any]:
    first = _txt(body.get("first_name"))
    last = _txt(body.get("last_name"))
    name = _txt(body.get("name") or body.get("full_name") or " ".join(p for p in (first, last) if p))
    provider = _txt(body.get("provider") or body.get("ads_provider") or body.get("source")).lower()
    campaign = _txt(body.get("campaign_id") or body.get("campaign") or body.get("utm_campaign"))
    utm_campaign = _txt(body.get("utm_campaign") or campaign)
    payload = {
        "name": name,
        "first_name": first or None,
        "last_name": last or None,
        "email": _txt(body.get("email")).lower() or None,
        "phone": _txt(body.get("phone")) or None,
        "provider": provider or None,
        "source": provider or _txt(body.get("source")) or "provider",
        "campaign_id": _txt(body.get("campaign_id")) or None,
        "ad_id": _txt(body.get("ad_id") or body.get("ad")) or None,
        "ad_group_id": _txt(body.get("ad_group_id") or body.get("adset_id") or body.get("ad_group")) or None,
        "medium": _txt(body.get("medium") or body.get("utm_medium") or "cpc") or None,
        "utm_source": _txt(body.get("utm_source") or provider) or None,
        "utm_medium": _txt(body.get("utm_medium") or body.get("medium") or "cpc") or None,
        "utm_campaign": utm_campaign or None,
        "click_id": _txt(body.get("click_id") or body.get("fbclid") or body.get("gclid") or body.get("ttclid")) or None,
        "external_id": _txt(body.get("external_id") or body.get("external_lead_id") or body.get("lead_id")) or None,
        "occurred_at": _txt(body.get("timestamp") or body.get("occurred_at") or body.get("submitted_at")) or None,
        "consent": body.get("consent") if isinstance(body.get("consent"), dict) else {"granted": bool(body.get("consent"))},
        "raw_provider_ref": _txt(body.get("raw_provider_ref") or body.get("raw_id")) or None,
        "project_key": _txt(body.get("project_key")) or "vanguard",
    }
    payload.update(touch_payload({**body, **payload}))
    return payload


def provider_duplicate_key(item: dict[str, Any]) -> tuple[str, str] | None:
    provider = _txt(item.get("provider") or item.get("source")).lower()
    ext = _txt(item.get("external_id"))
    if provider and ext:
        return provider, ext
    return None


def find_provider_duplicate(leads: list[dict[str, Any]], incoming: dict[str, Any]) -> dict[str, Any] | None:
    key = provider_duplicate_key(incoming)
    if key:
        for item in leads:
            if provider_duplicate_key(item) == key:
                return item
    email = _txt(incoming.get("email")).lower()
    phone = _txt(incoming.get("phone"))
    if email:
        for item in leads:
            if _txt(item.get("email")).lower() == email:
                return item
    if phone:
        for item in leads:
            if _txt(item.get("phone")) == phone:
                return item
    return None


def merge_duplicate(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Update last-touch only. Do not overwrite candidate/history fields."""
    patch = preserve_first_touch(existing, incoming)
    for field in ("click_id", "ad_id", "ad_group_id", "raw_provider_ref", "provider"):
        if not _txt(existing.get(field)) and _txt(incoming.get(field)):
            patch[field] = incoming.get(field)
    if incoming.get("consent") and not existing.get("consent"):
        patch["consent"] = incoming.get("consent")
    return patch
