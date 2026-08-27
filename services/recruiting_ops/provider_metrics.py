"""Normalize and persist provider metrics. Missing values stay None — never fake zero."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.recruiting_ops.provider_http import backoff_seconds

UNAVAILABLE = "UNAVAILABLE"


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float | None:
    if value in (None, "", [], {}):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def metric_bucket_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def normalize_metric_row(provider: str, raw: dict[str, Any], *, account: str | None = None) -> dict[str, Any]:
    metrics = raw.get("metrics") if isinstance(raw.get("metrics"), dict) else {}
    spend = _num(raw.get("spend") or raw.get("cost") or metrics.get("spend") or metrics.get("cost"))
    impressions = _num(raw.get("impressions") or metrics.get("impressions"))
    clicks = _num(raw.get("clicks") or metrics.get("clicks"))
    reach = _num(raw.get("reach") or metrics.get("reach"))
    conversions = _num(raw.get("conversions") or raw.get("conversion") or metrics.get("conversions") or metrics.get("conversion"))
    ctr = _num(raw.get("ctr") or metrics.get("ctr"))
    cpc = _num(raw.get("cpc") or raw.get("average_cpc") or metrics.get("cpc") or metrics.get("average_cpc"))
    cpm = _num(raw.get("cpm") or metrics.get("cpm"))
    campaign_id = _txt(raw.get("campaign_id") or raw.get("id") or (raw.get("campaign") or {}).get("id") or (raw.get("dimensions") or {}).get("campaign_id"))
    return {
        "provider": provider,
        "account": account or _txt(raw.get("account_id") or raw.get("advertiser_id")) or None,
        "campaign": _txt(raw.get("campaign_name") or raw.get("name") or (raw.get("campaign") or {}).get("name")) or None,
        "external_campaign_id": campaign_id or None,
        "bucket": _txt(raw.get("date_start") or raw.get("stat_time_day") or raw.get("bucket")) or metric_bucket_now(),
        "currency": _txt(raw.get("currency") or raw.get("account_currency")) or None,
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "reach": reach,
        "conversions": conversions,
        "ctr": ctr,
        "cpc": cpc,
        "cpm": cpm,
        "source": "LIVE",
        "unavailable": [name for name, value in (("reach", reach), ("conversions", conversions), ("cpm", cpm)) if value is None],
        "fake_data": False,
        "provider_metadata": {k: v for k, v in raw.items() if k not in {"spend", "impressions", "clicks"}},
    }


def metric_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            _txt(row.get("provider")),
            _txt(row.get("account")),
            _txt(row.get("external_campaign_id")),
            _txt(row.get("bucket")),
        ]
    )


def upsert_metrics(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {metric_key(item): item for item in existing}
    for row in incoming:
        index[metric_key(row)] = {**index.get(metric_key(row), {}), **row, "updated_at": datetime.now(timezone.utc).isoformat()}
    return list(index.values())


def aggregate_live_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "spend": None,
            "impressions": None,
            "clicks": None,
            "ctr": None,
            "cpc": None,
            "no_live_data": True,
            "source": UNAVAILABLE,
        }
    spend_vals = [item["spend"] for item in rows if item.get("spend") is not None]
    imp_vals = [item["impressions"] for item in rows if item.get("impressions") is not None]
    click_vals = [item["clicks"] for item in rows if item.get("clicks") is not None]
    spend = sum(spend_vals) if spend_vals else None
    impressions = sum(imp_vals) if imp_vals else None
    clicks = sum(click_vals) if click_vals else None
    ctr = (clicks / impressions) if clicks is not None and impressions else None
    cpc = (spend / clicks) if spend is not None and clicks else None
    return {
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": ctr,
        "cpc": cpc,
        "no_live_data": spend is None and impressions is None and clicks is None,
        "source": "LIVE",
    }


def next_sync_at(attempt: int) -> int:
    return backoff_seconds(attempt)
