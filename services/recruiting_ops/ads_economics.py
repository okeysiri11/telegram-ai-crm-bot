"""Vanguard advertising economics — internal campaigns, operator spend, no fake provider stats."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from services.recruiting_ops.attribution import is_test_traffic

CAMPAIGN_SOURCES = (
    "meta",
    "facebook",
    "instagram",
    "google",
    "tiktok",
    "organic",
    "direct",
    "referral",
    "other",
)

PROVIDER_BACKED_SOURCES = frozenset({"meta", "facebook", "instagram", "google", "tiktok"})
SOURCE_ALIASES = {
    "fb": "facebook",
    "meta ads": "meta",
    "facebook ads": "facebook",
    "ig": "instagram",
    "insta": "instagram",
    "google ads": "google",
    "tik tok": "tiktok",
    "paid_social": "instagram",
    "manual": "other",
}

SOURCE_LABEL_RU = {
    "meta": "Meta",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "google": "Google",
    "tiktok": "TikTok",
    "organic": "Organic",
    "direct": "Direct",
    "referral": "Referral",
    "other": "Other",
}

DATE_PRESETS = ("today", "7d", "30d", "this_month", "last_month", "custom")

PROVIDER_CONNECT_REQUIREMENTS = {
    "meta": {
        "label": "Meta Ads",
        "env": ["META_ADS_APP_ID", "META_ADS_APP_SECRET"],
        "message_ru": "Для подключения Meta Ads задайте META_ADS_APP_ID и META_ADS_APP_SECRET. OAuth не запускается без конфигурации.",
    },
    "google": {
        "label": "Google Ads",
        "env": ["GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_DEVELOPER_TOKEN"],
        "message_ru": "Для подключения Google Ads задайте GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET и GOOGLE_ADS_DEVELOPER_TOKEN. OAuth не запускается без developer token.",
    },
    "tiktok": {
        "label": "TikTok Ads",
        "env": ["TIKTOK_ADS_APP_ID", "TIKTOK_ADS_APP_SECRET"],
        "message_ru": "Для подключения TikTok Ads задайте TIKTOK_ADS_APP_ID и TIKTOK_ADS_APP_SECRET. OAuth не запускается без конфигурации.",
    },
}


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ratio(part: float | None, whole: float | None) -> float | None:
    if part is None or whole is None or whole <= 0:
        return None
    return round(part / whole, 6)


def normalize_source(raw: Any) -> str:
    value = _txt(raw).lower()
    value = SOURCE_ALIASES.get(value, value)
    return value if value in CAMPAIGN_SOURCES else "other"


def source_label(raw: Any) -> str:
    key = normalize_source(raw)
    return SOURCE_LABEL_RU[key]


def provider_backed(source: Any) -> bool:
    return normalize_source(source) in PROVIDER_BACKED_SOURCES


def _parse_iso_date(value: Any) -> date | None:
    text = _txt(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _parse_iso_dt(value: Any) -> datetime | None:
    text = _txt(value)
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        day = _parse_iso_date(text)
        if not day:
            return None
        return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)


def resolve_date_window(
    *,
    preset: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    now = today or datetime.now(timezone.utc).date()
    key = _txt(preset).lower() or "30d"
    if key not in DATE_PRESETS:
        key = "30d"
    start: date | None = None
    end: date | None = now
    if key == "today":
        start = now
    elif key == "7d":
        start = now - timedelta(days=6)
    elif key == "30d":
        start = now - timedelta(days=29)
    elif key == "this_month":
        start = now.replace(day=1)
    elif key == "last_month":
        first_this = now.replace(day=1)
        end = first_this - timedelta(days=1)
        start = end.replace(day=1)
    else:
        start = _parse_iso_date(date_from)
        end = _parse_iso_date(date_to) or now
        if start and end and start > end:
            start, end = end, start
    return {
        "preset": key,
        "from": start.isoformat() if start else None,
        "to": end.isoformat() if end else None,
        "start": start,
        "end": end,
        "unbounded": start is None and key == "custom",
    }


def in_window(value: Any, window: dict[str, Any]) -> bool:
    if window.get("unbounded") or window.get("start") is None:
        return True
    parsed = _parse_iso_dt(value)
    if parsed is None:
        return False
    day = parsed.date()
    start: date = window["start"]
    end: date = window["end"] or start
    return start <= day <= end


def item_in_window(item: dict[str, Any], window: dict[str, Any]) -> bool:
    if _txt(item.get("spent_on") or item.get("period_start") or item.get("amount")):
        marker = item.get("spent_on") or item.get("period_start")
        return True if not marker else in_window(marker, window)
    for key in ("submitted_at", "created_at"):
        if _txt(item.get(key)):
            return in_window(item.get(key), window)
    return True


def public_date_range(window: dict[str, Any]) -> dict[str, Any]:
    return {"preset": window.get("preset"), "from": window.get("from"), "to": window.get("to")}


def campaign_matches_lead(campaign: dict[str, Any], lead: dict[str, Any]) -> bool:
    cid = _txt(campaign.get("id"))
    if cid and _txt(lead.get("campaign_id")) == cid:
        return True
    codes = {
        _txt(campaign.get("campaign_code")).lower(),
        _txt(campaign.get("utm_campaign")).lower(),
        _txt((campaign.get("utm") or {}).get("campaign")).lower(),
    }
    codes.discard("")
    lead_codes = {
        _txt(lead.get("utm_campaign")).lower(),
        _txt(lead.get("first_touch_campaign")).lower(),
        _txt(lead.get("campaign_code")).lower(),
    }
    lead_codes.discard("")
    return bool(codes & lead_codes)


def funnel_economics(
    *,
    impressions: Any = None,
    clicks: Any = None,
    applications: int = 0,
    qualified: int = 0,
    interviews: int = 0,
    approved: int = 0,
    hired: int = 0,
    spend: Any = None,
) -> dict[str, Any]:
    imp = _num(impressions)
    clk = _num(clicks)
    spend_n = _num(spend)
    stages = [
        {"id": "impressions", "label_ru": "Показы", "count": None if imp is None else int(imp)},
        {"id": "clicks", "label_ru": "Клики", "count": None if clk is None else int(clk)},
        {"id": "applications", "label_ru": "Заявки", "count": applications},
        {"id": "qualified", "label_ru": "Квалифицированы", "count": qualified},
        {"id": "interviews", "label_ru": "Интервью", "count": interviews},
        {"id": "approved", "label_ru": "Одобрены", "count": approved},
        {"id": "hired", "label_ru": "Наняты", "count": hired},
    ]
    prev_count: int | None = None
    top = next((int(s["count"]) for s in stages if s["count"] is not None and int(s["count"]) > 0), None)
    for step in stages:
        count = step["count"]
        step["conversion_from_previous"] = ratio(float(count), float(prev_count)) if count is not None and prev_count is not None else None
        step["conversion_overall"] = ratio(float(count), float(top)) if count is not None and top is not None else None
        if count is not None:
            prev_count = int(count)
    return {
        "steps": stages,
        "impressions": None if imp is None else int(imp),
        "clicks": None if clk is None else int(clk),
        "applications": applications,
        "qualified": qualified,
        "interviews": interviews,
        "approved": approved,
        "hired": hired,
        "spend": spend_n,
        "ctr": ratio(clk, imp),
        "cpc": ratio(spend_n, clk),
        "cpl": ratio(spend_n, float(applications)) if applications else None,
        "cost_per_hire": ratio(spend_n, float(hired)) if hired else None,
        "conversion": ratio(float(hired), float(applications)) if applications else None,
        "fake_data": False,
        "missing_provider_metrics": imp is None and clk is None,
        "message_ru": "Нет данных провайдера" if imp is None and clk is None else None,
    }


def stage_bucket(candidate: dict[str, Any]) -> str:
    return _txt(candidate.get("pipeline_stage") or candidate.get("status")).upper()


def count_stages(candidates: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"qualified": 0, "interviews": 0, "approved": 0, "hired": 0}
    for item in candidates:
        stage = stage_bucket(item)
        if stage in {"QUALIFIED", "INTERVIEW", "APPROVED", "HIRED"}:
            counts["qualified"] += 1
        if stage in {"INTERVIEW", "APPROVED", "HIRED"}:
            counts["interviews"] += 1
        if stage in {"APPROVED", "HIRED"}:
            counts["approved"] += 1
        if stage == "HIRED":
            counts["hired"] += 1
    return counts


def recruiter_attribution(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in candidates:
        key = _txt(item.get("assignee") or item.get("assignee_id") or item.get("recruiter_id")) or "unassigned"
        groups.setdefault(key, []).append(item)
    rows = []
    for recruiter, items in sorted(groups.items(), key=lambda pair: pair[0]):
        stages = count_stages(items)
        rows.append(
            {
                "recruiter": None if recruiter == "unassigned" else recruiter,
                "recruiter_label": "Не назначен" if recruiter == "unassigned" else recruiter,
                "assigned_candidates": len(items),
                **stages,
            }
        )
    return rows


def source_from_lead(lead: dict[str, Any]) -> str:
    return normalize_source(lead.get("utm_source") or lead.get("first_touch_source") or lead.get("source"))


def source_economics(
    leads: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    spend_by_source: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    by_lead: dict[str, str] = {_txt(item.get("id")): source_from_lead(item) for item in leads}
    buckets: dict[str, dict[str, Any]] = {
        key: {"source": key, "label_ru": SOURCE_LABEL_RU[key], "applications": 0, "leads": [], "candidates": []}
        for key in CAMPAIGN_SOURCES
    }
    for lead in leads:
        src = source_from_lead(lead)
        buckets[src]["applications"] += 1
        buckets[src]["leads"].append(lead)
    for cand in candidates:
        lids = {_txt(cand.get("lead_id"))}
        lids.update(_txt(x) for x in (cand.get("lead_ids") or []) if x)
        src = None
        for lid in lids:
            if lid in by_lead:
                src = by_lead[lid]
                break
        src = src or normalize_source(cand.get("utm_source") or cand.get("source"))
        buckets[src]["candidates"].append(cand)
    spend_map = spend_by_source or {}
    rows = []
    for key in CAMPAIGN_SOURCES:
        bucket = buckets[key]
        stages = count_stages(bucket["candidates"])
        spend = spend_map.get(key)
        apps = bucket["applications"]
        rows.append(
            {
                "source": key,
                "label_ru": bucket["label_ru"],
                "applications": apps,
                "qualified": stages["qualified"],
                "interviews": stages["interviews"],
                "approved": stages["approved"],
                "hired": stages["hired"],
                "spend": spend,
                "cpl": ratio(spend, float(apps)) if spend is not None and apps else None,
                "cost_per_hire": ratio(spend, float(stages["hired"])) if spend is not None and stages["hired"] else None,
                "has_data": bool(apps or spend is not None),
            }
        )
    return rows


def sum_manual_spend(entries: list[dict[str, Any]], window: dict[str, Any] | None = None) -> float | None:
    total = 0.0
    found = False
    for item in entries:
        if window and not item_in_window(item, window):
            continue
        amount = _num(item.get("amount") if item.get("amount") is not None else item.get("spend"))
        if amount is None:
            continue
        total += amount
        found = True
    return round(total, 6) if found else None


def provider_connect_panel(connections: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    from services.recruiting_ops.provider_connections import public_card
    from services.recruiting_ops.provider_layer import app_prerequisites
    from services.recruiting_ops.provider_state import normalize_provider_status

    by_id = {}
    for item in connections or []:
        key = _txt(item.get("provider") or item.get("provider_id") or item.get("id")).lower()
        if key:
            by_id[key] = item
    rows = []
    for key, spec in PROVIDER_CONNECT_REQUIREMENTS.items():
        raw = by_id.get(key) or {"provider": key, "status": "NOT_CONFIGURED"}
        card = public_card(raw)
        status = normalize_provider_status(card.get("status"))
        if status == "CONNECTED" and not card.get("connected"):
            status = "AUTHORIZING"
        connected = bool(card.get("connected")) and status == "CONNECTED"
        app = app_prerequisites(key)
        rows.append(
            {
                "provider": key,
                "label": spec["label"],
                "status": status if connected else status,
                "connected": connected,
                "live_verified": bool(card.get("live_verified")),
                "account_id": card.get("account_id"),
                "connected_account_name": card.get("connected_account_name"),
                "currency": card.get("currency"),
                "timezone": card.get("timezone"),
                "permissions": card.get("scopes") or [],
                "token_expires_at": card.get("token_expires_at"),
                "last_check_at": card.get("last_check_at"),
                "last_sync_at": card.get("last_sync_at"),
                "last_error": card.get("last_error"),
                "tracking_status": "WAITING_PROVIDER" if not connected else _txt(card.get("tracking_status")) or "LIVE",
                "required_env": list(app.get("required_env") or spec["env"]),
                "message_ru": None if connected else (card.get("message_ru") or app.get("message_ru") or spec["message_ru"]),
                "connect_available": bool(app.get("connect_available")),
                "oauth_ready": bool(app.get("oauth_ready")),
                "developer_token_available": app.get("developer_token_available"),
                "wizard_progress": card.get("wizard_progress"),
                "button_ru": f"Подключить {spec['label']}",
                "spend_policy": "PREFER_PROVIDER" if connected else "MANUAL_ONLY",
            }
        )
    return rows
