"""Provider connection center — public cards, wizards, health. No secrets."""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.provider_adapters import LIVE_ADAPTERS, mock_providers_allowed
from services.recruiting_ops.provider_readiness import ads_readiness, messaging_readiness
from services.recruiting_ops.secret_store import credential_presence

_RUNTIME_CONNECTED: dict[str, bool] = {}

# Product overlay for this sprint: Telegram stays disabled. Adapter HTTP is unchanged.
TELEGRAM_FROZEN = True
TELEGRAM_FROZEN_MESSAGE_RU = "Telegram намеренно отключён и не блокирует готовность Recruiting."


def set_runtime_connected(provider: str, connected: bool) -> None:
    key = (provider or "").strip().lower()
    if not key:
        return
    if connected:
        _RUNTIME_CONNECTED[key] = True
    else:
        _RUNTIME_CONNECTED.pop(key, None)


def is_runtime_connected(provider: str) -> bool:
    key = (provider or "").strip().lower()
    if key == "telegram" and TELEGRAM_FROZEN:
        return False
    return bool(_RUNTIME_CONNECTED.get(key))


def reset_runtime_connections() -> None:
    _RUNTIME_CONNECTED.clear()


PROVIDERS = ("meta", "google", "tiktok", "telegram", "whatsapp", "email")

CONNECTION_TYPES = {
    "meta": "OAuth / access token",
    "google": "OAuth + developer token",
    "tiktok": "OAuth / access token",
    "telegram": "Bot API",
    "whatsapp": "Cloud API",
    "email": "SMTP / API",
}

WIZARD_FIELDS: dict[str, list[dict[str, Any]]] = {
    "meta": [
        {"id": "app_id", "label_ru": "App ID", "secret": False, "required": False},
        {"id": "app_secret", "label_ru": "App Secret", "secret": True, "required": False},
        {"id": "ad_account_id", "label_ru": "Ad Account ID", "secret": False, "required": True},
        {"id": "page_id", "label_ru": "Page / Business", "secret": False, "required": False},
        {"id": "access_token", "label_ru": "Токен доступа", "secret": True, "required": False},
        {"id": "scopes", "label_ru": "Разрешения", "secret": False, "required": False},
    ],
    "google": [
        {"id": "customer_id", "label_ru": "Customer ID", "secret": False, "required": True},
        {"id": "manager_id", "label_ru": "Manager account", "secret": False, "required": False},
        {"id": "client_id", "label_ru": "OAuth Client ID", "secret": False, "required": True},
        {"id": "client_secret", "label_ru": "OAuth Client Secret", "secret": True, "required": True},
        {"id": "refresh_token", "label_ru": "Refresh token", "secret": True, "required": False},
        {"id": "developer_token", "label_ru": "Developer token", "secret": True, "required": True},
    ],
    "tiktok": [
        {"id": "app_id", "label_ru": "App ID", "secret": False, "required": False},
        {"id": "app_secret", "label_ru": "App Secret", "secret": True, "required": False},
        {"id": "advertiser_id", "label_ru": "Advertiser account", "secret": False, "required": True},
        {"id": "access_token", "label_ru": "Токен / OAuth", "secret": True, "required": False},
    ],
    "telegram": [
        {"id": "bot_username", "label_ru": "Бот", "secret": False, "required": False},
        {"id": "target_chat", "label_ru": "Чат / канал", "secret": False, "required": False},
        {"id": "bot_token", "label_ru": "Токен бота", "secret": True, "required": True},
    ],
    "whatsapp": [
        {"id": "business_account_id", "label_ru": "Business account", "secret": False, "required": False},
        {"id": "phone_number_id", "label_ru": "Phone identifier", "secret": False, "required": True},
        {"id": "access_token", "label_ru": "API token", "secret": True, "required": True},
        {"id": "verify_token", "label_ru": "Webhook verify token", "secret": True, "required": False},
        {"id": "app_secret", "label_ru": "App Secret (подпись webhook)", "secret": True, "required": False},
    ],
    "email": [
        {"id": "provider_type", "label_ru": "Тип провайдера", "secret": False, "required": True},
        {"id": "smtp_host", "label_ru": "SMTP / API host", "secret": False, "required": True},
        {"id": "smtp_user", "label_ru": "Пользователь", "secret": False, "required": False},
        {"id": "email_from", "label_ru": "Отправитель", "secret": False, "required": True},
        {"id": "smtp_port", "label_ru": "Порт", "secret": False, "required": False},
        {"id": "tls_mode", "label_ru": "TLS/SSL", "secret": False, "required": False},
        {"id": "sender_name", "label_ru": "Имя отправителя", "secret": False, "required": False},
        {"id": "smtp_password", "label_ru": "Пароль SMTP", "secret": True, "required": False},
        {"id": "api_key", "label_ru": "API ключ (SendGrid/Mailgun/SES позже)", "secret": True, "required": False},
    ],
}

STATUS_RU = {
    "NOT_CONFIGURED": "Не настроено",
    "CONFIGURING": "Настройка",
    "CONNECTED": "Подключено",
    "DEGRADED": "Ограничено",
    "ERROR": "Ошибка",
    "DISABLED": "Отключено",
    "FROZEN": "Заморожено",
}


def _txt(value: Any) -> str:
    return str(value or "").strip()


def default_connection(provider: str) -> dict[str, Any]:
    adapter = LIVE_ADAPTERS[provider]
    return {
        "id": f"provider-{provider}",
        "provider": provider,
        "label": adapter.label,
        "label_ru": adapter.label,
        "status": "NOT_CONFIGURED",
        "status_label_ru": STATUS_RU["NOT_CONFIGURED"],
        "mode": "LIVE",
        "connection_type": CONNECTION_TYPES[provider],
        "account_id": None,
        "workspace_id": None,
        "enabled": False,
        "last_health_check_at": None,
        "last_successful_request_at": None,
        "last_error": None,
        "latency_ms": None,
        "credential_expiry": None,
        "scopes": [],
        "tracking_status": "WAITING_PROVIDER",
        "connected": False,
        "mock": False,
        "public": {},
    }


def public_card(row: dict[str, Any]) -> dict[str, Any]:
    provider = _txt(row.get("provider"))
    creds = credential_presence(provider)
    status = _txt(row.get("status") or "NOT_CONFIGURED").upper()
    mode = _txt(row.get("mode") or "LIVE").upper()
    if mode != "MOCK" and status == "CONNECTED":
        from services.recruiting_ops.runtime import is_production_runtime

        verified = bool(row.get("live_verified"))
        injected = bool(row.get("mocked_http")) and not is_production_runtime()
        if not verified and not injected:
            status = "CONFIGURING"
            row = {**row, "status": status, "connected": False}
    tracking = "DELIVERABLE" if status == "CONNECTED" else "WAITING_PROVIDER"
    card = {
        "provider": provider,
        "label": row.get("label") or LIVE_ADAPTERS.get(provider, LIVE_ADAPTERS["meta"]).label,
        "status": status,
        "status_label_ru": STATUS_RU.get(status, status),
        "mode": mode,
        "mode_label_ru": "MOCK" if mode == "MOCK" else "LIVE",
        "connection_type": row.get("connection_type") or CONNECTION_TYPES.get(provider),
        "account_id": row.get("account_id") or row.get("workspace_id"),
        "workspace_id": row.get("workspace_id") or row.get("account_id"),
        "last_successful_health_check": row.get("last_successful_request_at") or row.get("last_health_check_at"),
        "last_error": row.get("last_error"),
        "credential_presence": creds,
        "credential_expiry": creds.get("expires_at") or row.get("credential_expiry"),
        "permissions": list(row.get("scopes") or []),
        "scopes": list(row.get("scopes") or []),
        "tracking_status": tracking,
        "enabled": bool(row.get("enabled")),
        "connected": status == "CONNECTED",
        "mock": mode == "MOCK",
        "latency_ms": row.get("latency_ms"),
        "public": row.get("public") or {},
        "wizard": WIZARD_FIELDS.get(provider) or [],
        "capabilities": list(LIVE_ADAPTERS[provider].capabilities) if provider in LIVE_ADAPTERS else [],
        "actions": ["configure", "test", "reconnect", "disable", "diagnostics", "oauth"],
        "live_verified": bool(row.get("live_verified")),
        "mocked_http": bool(row.get("mocked_http")),
        "identity": row.get("identity") or {},
        "consecutive_failures": row.get("consecutive_failures") or 0,
        "frozen": False,
        "connect_cta": True,
    }
    if provider == "telegram" and TELEGRAM_FROZEN:
        card["status"] = "DISABLED"
        card["status_label_ru"] = "Отключено (заморожено)"
        card["connected"] = False
        card["enabled"] = False
        card["frozen"] = True
        card["connect_cta"] = False
        card["tracking_status"] = "WAITING_PROVIDER"
        card["actions"] = []
        card["message_ru"] = TELEGRAM_FROZEN_MESSAGE_RU
    return card


def is_provider_connected(provider: str, connections: list[dict[str, Any]] | None = None) -> bool:
    key = _txt(provider).lower()
    for row in connections or []:
        if _txt(row.get("provider")).lower() != key:
            continue
        if _txt(row.get("status")).upper() == "CONNECTED" and row.get("enabled") is not False:
            return True
    return False


def provider_health_snapshot(connections: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for provider in PROVIDERS:
        row = next((item for item in connections if _txt(item.get("provider")) == provider), default_connection(provider))
        card = public_card(row)
        items.append(
            {
                "provider": provider,
                "mode": card["mode"],
                "connection_status": card["status"],
                "last_check": card["last_successful_health_check"],
                "latency": card["latency_ms"],
                "last_successful_request": card["last_successful_health_check"],
                "last_error": card["last_error"],
                "credential_expiry_warning": bool(card.get("credential_expiry")),
                "connected": card["connected"],
                "mock": card["mock"],
            }
        )
    connected = sum(1 for item in items if item["connected"])
    return {
        "ok": True,
        "items": items,
        "connected_count": connected,
        "infra_independent": True,
        "message_ru": "Состояние провайдеров не меняет статус ядра инфраструктуры.",
    }


def connection_center_payload(connections: list[dict[str, Any]]) -> dict[str, Any]:
    cards = []
    by_provider = { _txt(item.get("provider")): item for item in connections }
    from services.recruiting_ops.provider_oauth import OAUTH_PROVIDERS, oauth_ready, redirect_uri

    for provider in PROVIDERS:
        card = public_card(by_provider.get(provider) or default_connection(provider))
        if provider in OAUTH_PROVIDERS:
            card["oauth_ready"] = oauth_ready(provider)
            card["redirect_uri"] = redirect_uri(provider)
            card["actions"] = list(card.get("actions") or []) + ([] if "oauth" in (card.get("actions") or []) else [])
        cards.append(card)
    return {
        "ok": True,
        "items": cards,
        "mock_allowed": mock_providers_allowed(),
        "fake_data": False,
    }


def env_readiness_overlay() -> dict[str, Any]:
    ads = ads_readiness()["providers"]
    msg = messaging_readiness()["channels"]
    return {**ads, **{k: {**v, "provider": k} for k, v in msg.items()}}


def wizard_spec(provider: str) -> dict[str, Any]:
    key = _txt(provider).lower()
    if key not in WIZARD_FIELDS:
        return {"ok": False, "error": "not_found", "message_ru": "Неизвестный провайдер"}
    return {
        "ok": True,
        "provider": key,
        "label": LIVE_ADAPTERS[key].label,
        "fields": WIZARD_FIELDS[key],
        "test_required": True,
        "persist_browser": False,
        "message_ru": "Секреты не сохраняются в браузере.",
    }
