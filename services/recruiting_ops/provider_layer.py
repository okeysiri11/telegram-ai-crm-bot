"""Read-only ads provider layer: mapping, spend policy, FX, sync refuse, diagnostics."""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.provider_oauth import oauth_ready
from services.recruiting_ops.provider_state import ADS_PROVIDERS, normalize_provider_status, status_label_ru
from services.recruiting_ops.secret_store import credential_presence

MAPPING_STATES = ("UNMAPPED", "SUGGESTED", "MAPPED", "CONFLICT")
ATTRIBUTION_QUALITY = ("EXACT", "UTM_MATCH", "PROVIDER_MATCH", "MANUAL", "UNKNOWN")
SPEND_ORIGINS = ("MANUAL", "PROVIDER", "ADJUSTMENT")
SPEND_POLICIES = ("PREFER_PROVIDER", "MANUAL_ONLY", "PROVIDER_ONLY", "CUSTOM_ADJUSTED")
WIZARD_STEPS = (
    {"id": "prerequisites", "label_ru": "Предварительные условия"},
    {"id": "authorize", "label_ru": "Авторизация"},
    {"id": "select_account", "label_ru": "Выбор аккаунта"},
    {"id": "verify_permissions", "label_ru": "Проверка прав"},
    {"id": "live_test", "label_ru": "Живая проверка"},
    {"id": "enable_sync", "label_ru": "Включить синхронизацию"},
)

PROVIDER_APP_ENV = {
    "meta": ["META_ADS_APP_ID", "META_ADS_APP_SECRET"],
    "google": ["GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_DEVELOPER_TOKEN"],
    "tiktok": ["TIKTOK_ADS_APP_ID", "TIKTOK_ADS_APP_SECRET"],
}

ADAPTER_METHODS = (
    "connect",
    "disconnect",
    "refresh_credentials",
    "verify_connection",
    "list_accounts",
    "get_account_info",
    "list_campaigns",
    "get_campaign_metrics",
    "get_account_metrics",
    "get_sync_health",
)


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _txt(value).lower()


def default_spend_policy(*, connected: bool) -> str:
    return "PREFER_PROVIDER" if connected else "MANUAL_ONLY"


def resolve_spend(
    *,
    manual: float | None,
    provider: float | None,
    policy: str | None = None,
    connected: bool = False,
) -> dict[str, Any]:
    chosen = (policy or default_spend_policy(connected=connected)).upper()
    if chosen not in SPEND_POLICIES:
        chosen = default_spend_policy(connected=connected)
    amount = None
    origin = None
    if chosen == "MANUAL_ONLY":
        amount, origin = manual, "MANUAL" if manual is not None else None
    elif chosen == "PROVIDER_ONLY":
        amount, origin = provider, "PROVIDER" if provider is not None else None
    elif chosen == "CUSTOM_ADJUSTED":
        if manual is not None and provider is not None:
            amount, origin = provider, "CUSTOM_ADJUSTED"
        elif provider is not None:
            amount, origin = provider, "PROVIDER"
        elif manual is not None:
            amount, origin = manual, "MANUAL"
    else:  # PREFER_PROVIDER
        if provider is not None:
            amount, origin = provider, "PROVIDER"
        elif manual is not None:
            amount, origin = manual, "MANUAL"
    return {
        "amount": amount,
        "origin": origin,
        "policy": chosen,
        "manual": manual,
        "provider": provider,
        "stacked": False,
        "message_ru": None
        if amount is not None
        else ("Нет живых данных провайдера" if chosen in {"PREFER_PROVIDER", "PROVIDER_ONLY"} else "Нет расхода оператора"),
    }


def fx_normalize(amount: float | None, *, source_currency: str | None, reporting_currency: str | None) -> dict[str, Any]:
    src = _txt(source_currency).upper() or None
    dst = _txt(reporting_currency).upper() or src
    if amount is None:
        return {
            "amount": None,
            "source_currency": src,
            "normalized_currency": dst,
            "fx_rate_used": None,
            "fx_date": None,
            "normalization_status": "UNAVAILABLE",
            "message_ru": "Нормализация валюты недоступна.",
        }
    if src and dst and src != dst:
        return {
            "amount": None,
            "source_currency": src,
            "normalized_currency": dst,
            "fx_rate_used": None,
            "fx_date": None,
            "normalization_status": "UNAVAILABLE",
            "native_amount": amount,
            "message_ru": "Курс FX не задан — показана исходная валюта.",
        }
    return {
        "amount": amount,
        "source_currency": src,
        "normalized_currency": dst or src,
        "fx_rate_used": 1.0 if src and dst and src == dst else None,
        "fx_date": None,
        "normalization_status": "NATIVE" if src else "UNAVAILABLE",
        "message_ru": None,
    }


def suggest_campaign_mapping(external: dict[str, Any], internals: list[dict[str, Any]]) -> dict[str, Any]:
    ext_id = _txt(external.get("external_id") or external.get("id") or external.get("campaign_external_id"))
    ext_name = _norm(external.get("name") or external.get("campaign_name"))
    ext_utm = _norm(external.get("utm_campaign"))
    exact = [
        item
        for item in internals
        if ext_id and _txt(item.get("external_id") or item.get("provider_campaign_id")) == ext_id
    ]
    if len(exact) == 1:
        return {
            "state": "SUGGESTED",
            "internal_campaign_id": exact[0].get("id"),
            "quality": "EXACT",
            "ambiguous": False,
        }
    if len(exact) > 1:
        return {"state": "CONFLICT", "internal_campaign_id": None, "quality": "EXACT", "ambiguous": True, "candidates": [i.get("id") for i in exact]}
    utm_hits = [
        item
        for item in internals
        if ext_utm and _norm(item.get("utm_campaign") or item.get("campaign_code")) == ext_utm
    ]
    if len(utm_hits) == 1:
        return {
            "state": "SUGGESTED",
            "internal_campaign_id": utm_hits[0].get("id"),
            "quality": "UTM_MATCH",
            "ambiguous": False,
        }
    if len(utm_hits) > 1:
        return {"state": "CONFLICT", "internal_campaign_id": None, "quality": "UTM_MATCH", "ambiguous": True}
    name_hits = [item for item in internals if ext_name and _norm(item.get("name")) == ext_name]
    if len(name_hits) == 1:
        return {
            "state": "SUGGESTED",
            "internal_campaign_id": name_hits[0].get("id"),
            "quality": "PROVIDER_MATCH",
            "ambiguous": False,
        }
    if len(name_hits) > 1:
        return {"state": "CONFLICT", "internal_campaign_id": None, "quality": "PROVIDER_MATCH", "ambiguous": True}
    return {"state": "UNMAPPED", "internal_campaign_id": None, "quality": "UNKNOWN", "ambiguous": False}


def attribution_quality(*, campaign_id: str | None = None, utm_campaign: str | None = None, mapped: bool = False, manual: bool = False) -> str:
    if mapped and campaign_id:
        return "EXACT"
    if utm_campaign:
        return "UTM_MATCH"
    if campaign_id:
        return "PROVIDER_MATCH"
    if manual:
        return "MANUAL"
    return "UNKNOWN"


def refuse_sync(provider: str, *, configured: bool, connected: bool, account_selected: bool) -> dict[str, Any] | None:
    if not configured:
        return {
            "ok": False,
            "error": "NOT_CONFIGURED",
            "status": "NOT_CONFIGURED",
            "fake_data": False,
            "mocked": False,
            "message_ru": f"{provider}: синхронизация недоступна — провайдер не настроен.",
        }
    if not connected or not account_selected:
        return {
            "ok": False,
            "error": "NOT_CONFIGURED",
            "status": "WAITING_PROVIDER",
            "fake_data": False,
            "mocked": False,
            "message_ru": f"{provider}: нет проверенного аккаунта. Синхронизация не запущена.",
        }
    return None


def app_prerequisites(provider: str) -> dict[str, Any]:
    key = _txt(provider).lower()
    env = list(PROVIDER_APP_ENV.get(key) or [])
    ready = oauth_ready(key) if key in ADS_PROVIDERS else False
    if key == "google":
        creds = credential_presence("google")
        fields = creds.get("fields") or {}
        developer = bool((fields.get("developer_token") or {}).get("present"))
        return {
            "provider": key,
            "oauth_ready": ready,
            "developer_token_available": developer,
            "required_env": env,
            "connect_available": bool(ready and developer),
            "message_ru": None
            if ready and developer
            else (
                "Для Google Ads задайте GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET и GOOGLE_ADS_DEVELOPER_TOKEN. OAuth не запускается без developer token."
                if not developer
                else "Для подключения Google Ads задайте OAuth client credentials."
            ),
        }
    return {
        "provider": key,
        "oauth_ready": ready,
        "developer_token_available": None,
        "required_env": env,
        "connect_available": ready,
        "message_ru": None
        if ready
        else f"Для подключения задайте {', '.join(env)}. OAuth не запускается без конфигурации приложения.",
    }


def wizard_progress(*, app_ready: bool, authorized: bool, account_selected: bool, verified: bool, sync_enabled: bool) -> dict[str, Any]:
    done = 0
    if app_ready:
        done = 1
    if authorized:
        done = 2
    if account_selected:
        done = 3
    if verified:
        done = 4
    if sync_enabled and verified:
        done = 6
    steps = []
    for index, spec in enumerate(WIZARD_STEPS, start=1):
        steps.append({**spec, "index": index, "complete": index <= done, "current": index == min(done + 1, 6)})
    return {
        "steps": steps,
        "current_step": min(done + 1, 6),
        "complete": done == 6,
        "done_label_ru": "Готово" if done == 6 else None,
    }


def safe_diagnostics(row: dict[str, Any], *, app: dict[str, Any], creds: dict[str, Any]) -> dict[str, Any]:
    status = normalize_provider_status(row.get("status"))
    account = _txt(row.get("account_id") or row.get("connected_account_id"))
    verified = bool(row.get("live_verified")) and status == "CONNECTED"
    return {
        "provider": _txt(row.get("provider")).lower(),
        "auth_configured": bool(app.get("oauth_ready") or app.get("connect_available")),
        "tenant_credentials_present": bool(creds.get("any_present") or creds.get("present")),
        "token_valid": bool(creds.get("present")) and status not in {"TOKEN_EXPIRED", "NOT_CONFIGURED", "DISCONNECTED"},
        "account_selected": bool(account),
        "permissions_valid": bool(row.get("scopes")) if row.get("scopes") else None,
        "api_reachable": verified,
        "rate_limit_state": row.get("rate_limit_state") or "UNKNOWN",
        "last_sync": row.get("last_sync_at"),
        "last_error": row.get("last_error"),
        "connected": verified,
        "status": status,
        "status_label_ru": status_label_ru(status),
        "message_ru": row.get("last_error")
        or app.get("message_ru")
        or ("Провайдер подключён." if verified else "Провайдер не подключён. Живые данные недоступны."),
        "secrets": None,
        "fake_data": False,
    }


def normalize_metric_schema(row: dict[str, Any], *, provider: str) -> dict[str, Any]:
    def _num(value: Any) -> float | None:
        if value is None or str(value).strip() == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    return {
        "provider": _txt(provider).lower(),
        "account_id": _txt(row.get("account_id") or row.get("account")) or None,
        "campaign_external_id": _txt(row.get("campaign_external_id") or row.get("external_id") or row.get("id")) or None,
        "campaign_name": _txt(row.get("campaign_name") or row.get("name")) or None,
        "date": _txt(row.get("date") or row.get("bucket")) or None,
        "impressions": _num(row.get("impressions")),
        "clicks": _num(row.get("clicks")),
        "spend": _num(row.get("spend")),
        "currency": _txt(row.get("currency")).upper() or None,
        "provider_status": _txt(row.get("provider_status") or row.get("status")) or None,
        "synced_at": _txt(row.get("synced_at")) or None,
        "fake_data": False,
    }
