"""Recruiting campaign domain model — provider sync is separate from status."""

from __future__ import annotations

from typing import Any

CAMPAIGN_STATUSES = ("DRAFT", "READY", "ACTIVE", "PAUSED", "COMPLETED", "FAILED")
SYNC_STATES = ("NOT_SYNCED", "PENDING", "SYNCED", "ERROR")
STATUS_RU = {
    "DRAFT": "Черновик",
    "READY": "Готова",
    "ACTIVE": "Активна",
    "PAUSED": "Пауза",
    "COMPLETED": "Завершена",
    "FAILED": "Ошибка",
}


def _txt(value: Any) -> str:
    return str(value or "").strip()


def normalize_campaign_status(raw: Any, default: str = "DRAFT") -> str:
    value = _txt(raw).upper()
    aliases = {"active": "ACTIVE", "paused": "PAUSED", "draft": "DRAFT", "ready": "READY"}
    value = aliases.get(_txt(raw).lower(), value)
    return value if value in CAMPAIGN_STATUSES else default


def normalize_campaign(body: dict[str, Any], *, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    base = dict(existing or {})
    provider = _txt(body.get("provider") or body.get("ads_provider") or base.get("provider")).lower() or None
    status = normalize_campaign_status(body.get("status") or base.get("status") or "DRAFT")
    return {
        "provider": provider,
        "external_id": _txt(body.get("external_id") or base.get("external_id")) or None,
        "name": _txt(body.get("name") or base.get("name")),
        "objective": _txt(body.get("objective") or base.get("objective")) or None,
        "status": status,
        "status_label_ru": STATUS_RU[status],
        "budget": body.get("budget", base.get("budget")),
        "currency": _txt(body.get("currency") or base.get("currency") or "USD") or "USD",
        "start_at": _txt(body.get("start_at") or body.get("start_date") or base.get("start_at") or base.get("start_date")) or None,
        "end_at": _txt(body.get("end_at") or body.get("end_date") or base.get("end_at") or base.get("end_date")) or None,
        "targeting": body.get("targeting") if "targeting" in body else base.get("targeting"),
        "creative_refs": body.get("creative_refs") or body.get("creative_references") or base.get("creative_refs") or [],
        "landing_destination": _txt(body.get("landing_destination") or body.get("landing_url") or base.get("landing_destination") or base.get("landing_url")) or None,
        "utm": {
            "source": _txt(body.get("utm_source") or (body.get("utm") or {}).get("source") or base.get("utm_source")) or None,
            "medium": _txt(body.get("utm_medium") or (body.get("utm") or {}).get("medium") or base.get("utm_medium") or base.get("medium")) or None,
            "campaign": _txt(body.get("utm_campaign") or body.get("campaign_code") or (body.get("utm") or {}).get("campaign") or base.get("campaign_code")) or None,
        },
        "sync_state": _txt(body.get("sync_state") or base.get("sync_state") or "NOT_SYNCED").upper() if _txt(body.get("sync_state") or base.get("sync_state") or "NOT_SYNCED").upper() in SYNC_STATES else "NOT_SYNCED",
        "created_by": _txt(body.get("created_by") or base.get("created_by")) or None,
        "ads_api": "not_connected" if not provider else base.get("ads_api") or "not_connected",
    }
