"""Canonical ads-provider connection states. CONNECTED only after live verify."""

from __future__ import annotations

from typing import Any

CANONICAL_STATES = (
    "NOT_CONFIGURED",
    "WAITING_PROVIDER",
    "AUTHORIZING",
    "CONNECTED",
    "TOKEN_EXPIRED",
    "PERMISSION_ERROR",
    "API_ERROR",
    "DISCONNECTED",
)

STATUS_RU = {
    "NOT_CONFIGURED": "Не настроено",
    "WAITING_PROVIDER": "Ожидает провайдера",
    "AUTHORIZING": "Авторизация",
    "CONNECTED": "Подключено",
    "TOKEN_EXPIRED": "Токен истёк",
    "PERMISSION_ERROR": "Нет прав",
    "API_ERROR": "Ошибка API",
    "DISCONNECTED": "Отключено",
    "CONFIGURING": "Настройка",
    "DISABLED": "Отключено",
    "FROZEN": "Заморожено",
    "ERROR": "Ошибка",
    "DEGRADED": "Ограничено",
}

LEGACY_TO_CANONICAL = {
    "CONFIGURING": "AUTHORIZING",
    "ERROR": "API_ERROR",
    "DEGRADED": "API_ERROR",
    "DISABLED": "DISCONNECTED",
    "FROZEN": "DISCONNECTED",
}

ADS_PROVIDERS = ("meta", "google", "tiktok")


def _txt(value: Any) -> str:
    return str(value or "").strip()


def normalize_provider_status(raw: Any) -> str:
    value = _txt(raw).upper() or "NOT_CONFIGURED"
    value = LEGACY_TO_CANONICAL.get(value, value)
    return value if value in CANONICAL_STATES else "NOT_CONFIGURED"


def status_label_ru(raw: Any) -> str:
    key = normalize_provider_status(raw)
    return STATUS_RU.get(key, key)


def status_from_error(error: Any) -> str:
    code = _txt(error).upper()
    if code in {"TOKEN_EXPIRED", "EXPIRED", "TOKEN_EXPIRED_ERROR"}:
        return "TOKEN_EXPIRED"
    if code in {"PERMISSION_ERROR", "AUTH_ERROR", "FORBIDDEN", "INSUFFICIENT_PERMISSION"}:
        return "PERMISSION_ERROR"
    if code in {"NOT_CONFIGURED", "NOT_CONNECTED"}:
        return "NOT_CONFIGURED"
    if code:
        return "API_ERROR"
    return "NOT_CONFIGURED"


def public_connection_fields(row: dict[str, Any]) -> dict[str, Any]:
    status = normalize_provider_status(row.get("status"))
    connected = status == "CONNECTED" and bool(row.get("live_verified"))
    if not connected and status == "CONNECTED":
        status = "AUTHORIZING"
    return {
        "provider": _txt(row.get("provider")).lower(),
        "tenant_id": row.get("tenant_id") or row.get("organization_id"),
        "status": status,
        "status_label_ru": status_label_ru(status),
        "connected": connected,
        "connected_account_id": row.get("account_id") or row.get("connected_account_id"),
        "connected_account_name": row.get("connected_account_name") or (row.get("identity") or {}).get("name"),
        "currency": row.get("currency"),
        "timezone": row.get("timezone"),
        "connected_at": row.get("connected_at"),
        "last_check_at": row.get("last_health_check_at") or row.get("last_check_at"),
        "last_success_at": row.get("last_successful_request_at") or row.get("last_success_at"),
        "last_error": row.get("last_error"),
        "token_expires_at": row.get("token_expires_at") or row.get("credential_expiry"),
        "scopes": list(row.get("scopes") or []),
        "credential_version": row.get("credential_version") or 1,
        "sync_enabled": bool(row.get("sync_enabled")),
        "sync_cursor": row.get("sync_cursor"),
        "live_verified": bool(row.get("live_verified")) and connected,
    }
