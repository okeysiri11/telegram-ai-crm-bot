"""Normalized provider error codes. Never include secret values."""

from __future__ import annotations

from typing import Any

AUTH_ERROR = "AUTH_ERROR"
PERMISSION_ERROR = "PERMISSION_ERROR"
RATE_LIMITED = "RATE_LIMITED"
INVALID_ACCOUNT = "INVALID_ACCOUNT"
TOKEN_EXPIRED = "TOKEN_EXPIRED"
PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
UNKNOWN_PROVIDER_ERROR = "UNKNOWN_PROVIDER_ERROR"

RU = {
    AUTH_ERROR: "Ошибка авторизации провайдера.",
    PERMISSION_ERROR: "Недостаточно прав у провайдера.",
    RATE_LIMITED: "Провайдер ограничил частоту запросов.",
    INVALID_ACCOUNT: "Указан неверный рекламный аккаунт.",
    TOKEN_EXPIRED: "Срок действия токена истёк.",
    PROVIDER_UNAVAILABLE: "Провайдер недоступен.",
    UNKNOWN_PROVIDER_ERROR: "Неизвестная ошибка провайдера.",
}


def _blob(payload: Any) -> str:
    return str(payload or "").lower()


def classify_http_error(status: int | None, payload: Any = None) -> str:
    text = _blob(payload)
    code = int(status or 0)
    if "expired" in text or "token expired" in text or "invalid_grant" in text:
        return TOKEN_EXPIRED
    if "permission" in text or "insufficient" in text or code == 403:
        return PERMISSION_ERROR
    if "rate" in text or code == 429:
        return RATE_LIMITED
    if "invalid account" in text or "unknown user" in text or "does not exist" in text:
        return INVALID_ACCOUNT
    if code in {401, 400} and any(part in text for part in ("oauth", "auth", "token", "unauthorized")):
        return AUTH_ERROR
    if code == 401:
        return AUTH_ERROR
    if code >= 500:
        return PROVIDER_UNAVAILABLE
    if code == 0:
        return PROVIDER_UNAVAILABLE
    return UNKNOWN_PROVIDER_ERROR


def safe_error_message(code: str) -> str:
    return RU.get(code, RU[UNKNOWN_PROVIDER_ERROR])
