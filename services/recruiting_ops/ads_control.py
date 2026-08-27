"""Advertising control-center calculations — no live provider APIs."""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.ads_foundation import ADS_PROVIDERS, ENTITY_TYPES, ads_foundation

ADS_KINDS = ("ad_account", "ad_set", "creative", "audience", "ads_metrics")


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct(part: float | None, whole: float | None) -> float | None:
    if part is None or whole is None or whole <= 0:
        return None
    return round(part / whole, 6)


def campaign_costs(*, spend: Any, impressions: Any, clicks: Any, applications: int, leads: int, candidates: int) -> dict[str, Any]:
    spend_n = _num(spend)
    impressions_n = _num(impressions)
    clicks_n = _num(clicks)
    missing_provider = impressions_n is None and clicks_n is None
    return {
        "spend": spend_n,
        "impressions": impressions_n,
        "clicks": clicks_n,
        "applications": applications,
        "leads": leads,
        "candidates": candidates,
        "ctr": _pct(clicks_n, impressions_n),
        "cpc": _pct(spend_n, clicks_n),
        "cpl": _pct(spend_n, float(leads)) if leads else None,
        "cost_per_candidate": _pct(spend_n, float(candidates)) if candidates else None,
        "missing_provider_metrics": missing_provider,
        "message_ru": "Нет данных провайдера" if missing_provider else None,
        "fake_data": False,
    }


def control_center(*, project_key: str = "vanguard", campaigns: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    foundation = ads_foundation(project_key=project_key)
    return {
        **foundation,
        "control_center": True,
        "campaigns": campaigns or [],
        "entity_types": list(ENTITY_TYPES),
        "providers": foundation["providers"],
        "connected": False,
        "message_ru": "Провайдер не подключен",
        "fake_data": False,
    }


def normalize_ads_entity(kind: str, body: dict[str, Any], *, project_key: str) -> dict[str, Any] | dict[str, Any]:
    key = _txt(kind).lower()
    if key not in ADS_KINDS:
        return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип рекламной сущности"}
    provider = _txt(body.get("provider") or body.get("ads_provider")).lower()
    if provider and provider not in ADS_PROVIDERS:
        return {"ok": False, "error": "validation", "message_ru": "Неизвестный рекламный провайдер"}
    return {
        "ok": True,
        "item": {
            "name": _txt(body.get("name") or body.get("title")) or key,
            "provider": provider or None,
            "project_key": _txt(body.get("project_key")) or project_key,
            "campaign_id": _txt(body.get("campaign_id")) or None,
            "external_id": _txt(body.get("external_id")) or None,
            "status": _txt(body.get("status")) or "not_connected",
            "ads_api": "not_connected",
            "metrics": None,
            "fake_data": False,
            "message_ru": "Провайдер не подключен",
        },
    }
