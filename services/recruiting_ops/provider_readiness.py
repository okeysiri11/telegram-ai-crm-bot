"""Secure provider readiness for ads, messaging, and anti-bot.

Does not call live Meta/Google/TikTok APIs.
Never logs tokens, client secrets, refresh tokens or API secrets.
"""

from __future__ import annotations

import os
from typing import Any

from services.recruiting_ops.antibot import FUTURE_PROVIDERS, provider_secret, resolve_provider
from services.recruiting_ops.runtime import is_production_runtime

SECRET_ENV_NAMES = {
    "META_ADS_ACCESS_TOKEN",
    "META_ADS_APP_SECRET",
    "META_APP_SECRET",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "TIKTOK_ADS_ACCESS_TOKEN",
    "TIKTOK_ADS_APP_SECRET",
    "VANGUARD_TELEGRAM_BOT_TOKEN",
    "WHATSAPP_TOKEN",
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_VERIFY_TOKEN",
    "WHATSAPP_APP_SECRET",
    "SMTP_PASSWORD",
    "VANGUARD_ANTIBOT_SECRET",
    "TURNSTILE_SECRET_KEY",
    "HCAPTCHA_SECRET",
    "RECAPTCHA_SECRET_KEY",
    "VANGUARD_INGEST_SECRET",
}

ADS_SPECS = {
    "meta": {
        "label": "Meta Ads",
        "secret": ["META_ADS_ACCESS_TOKEN"],
        "public": ["META_ADS_ACCOUNT_ID"],
    },
    "google": {
        "label": "Google Ads",
        "secret": ["GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN", "GOOGLE_ADS_DEVELOPER_TOKEN"],
        "public": ["GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CUSTOMER_ID"],
    },
    "tiktok": {
        "label": "TikTok Ads",
        "secret": ["TIKTOK_ADS_ACCESS_TOKEN"],
        "public": ["TIKTOK_ADS_ADVERTISER_ID"],
    },
}

MESSAGING_SPECS = {
    "telegram": {
        "label": "Telegram",
        "secret": ["VANGUARD_TELEGRAM_BOT_TOKEN"],
        "public": [],
    },
    "whatsapp": {
        "label": "WhatsApp",
        "secret": ["WHATSAPP_ACCESS_TOKEN"],
        "public": ["WHATSAPP_PHONE_NUMBER_ID"],
    },
    "email": {
        "label": "Email",
        "secret": ["SMTP_PASSWORD"],
        "public": ["SMTP_HOST", "SMTP_USER", "EMAIL_FROM"],
    },
}

RU = {
    "NOT_CONFIGURED": "Не настроено",
    "CONFIGURED": "Ограничено",
    "CONNECTED": "Работает",
    "DEGRADED": "Ограничено",
    "ERROR": "Ошибка",
}


def _present(name: str) -> bool:
    if name == "WHATSAPP_ACCESS_TOKEN":
        return bool((os.getenv("WHATSAPP_ACCESS_TOKEN") or os.getenv("WHATSAPP_TOKEN") or "").strip())
    return bool((os.getenv(name) or "").strip())


def _env_status(secret: list[str], public: list[str]) -> dict[str, Any]:
    missing_public = [name for name in public if not _present(name)]
    secrets_ok = all(_present(name) for name in secret) if secret else True
    public_ok = not missing_public
    if not secrets_ok and not any(_present(n) for n in public + secret):
        code = "NOT_CONFIGURED"
    elif not secrets_ok or not public_ok:
        code = "NOT_CONFIGURED"
    else:
        code = "CONFIGURED"
    return {
        "code": code,
        "label_ru": RU[code],
        "configured_secrets": secrets_ok,
        "missing": missing_public,
        "connected": False,
        "live_api": False,
    }


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        upper = str(key).upper()
        lowered = str(key).lower()
        if upper in SECRET_ENV_NAMES or any(part in lowered for part in ("token", "secret", "password", "refresh")):
            out[key] = True if value else False
        elif isinstance(value, dict):
            out[key] = redact_mapping(value)
        else:
            out[key] = value
    return out


def ads_readiness() -> dict[str, Any]:
    providers = {}
    for key, spec in ADS_SPECS.items():
        status = _env_status(spec["secret"], spec["public"])
        providers[key] = {
            "provider": key,
            "label": spec["label"],
            "status": status["code"],
            "label_ru": status["label_ru"],
            "missing": status["missing"],
            "configured_secrets": status["configured_secrets"],
            "connected": False,
            "fake_data": False,
            "message_ru": "Провайдер не подключен" if status["code"] == "NOT_CONFIGURED" else "Учётные данные заданы, live API не вызывался.",
        }
    return {"ok": True, "providers": providers, "connected": False, "fake_data": False}


def messaging_readiness() -> dict[str, Any]:
    channels = {}
    for key, spec in MESSAGING_SPECS.items():
        status = _env_status(spec["secret"], spec["public"])
        channels[key] = {
            "channel": key,
            "label": spec["label"],
            "status": status["code"],
            "label_ru": status["label_ru"],
            "missing": status["missing"],
            "configured_secrets": status["configured_secrets"],
            "journal_only": True,
            "sent": False,
            "connected": False,
            "message_ru": "Только журнал. Отправка не подтверждена провайдером.",
        }
    return {"ok": True, "channels": channels}


def antibot_readiness() -> dict[str, Any]:
    provider = resolve_provider()
    secret = bool(provider_secret())
    missing: list[str] = []
    if provider in {"none", ""}:
        missing.append("VANGUARD_ANTIBOT_PROVIDER")
    if provider in FUTURE_PROVIDERS and not secret:
        missing.append("VANGUARD_ANTIBOT_SECRET")
    if provider in FUTURE_PROVIDERS and secret:
        code = "CONFIGURED"
        message = "Секрет задан, коммерческий адаптер ещё не вызывает провайдера."
    elif provider == "test" and not is_production_runtime():
        code = "CONFIGURED"
        message = "Тестовый антибот (только development)."
    else:
        code = "NOT_CONFIGURED"
        message = "Антибот не настроен."
    return {
        "ok": True,
        "provider": provider if provider != "none" else None,
        "status": code,
        "label_ru": RU[code],
        "captcha_active": False,
        "missing": missing,
        "required": is_production_runtime(),
        "message_ru": message,
    }
