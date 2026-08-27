"""Provider-independent anti-bot for public Vanguard apply.

Adapters (future): Cloudflare Turnstile, hCaptcha, reCAPTCHA.
This sprint ships the verification interface only.

- Development may use provider=test with token vanguard-test-pass.
- Production fails closed if anti-bot is required and no real provider secret is set.
- Never reports captcha_active=true unless a real provider is configured.
"""

from __future__ import annotations

import os
from typing import Any

from services.recruiting_ops.runtime import is_production_runtime

TEST_TOKEN = "vanguard-test-pass"
FUTURE_PROVIDERS = ("turnstile", "hcaptcha", "recaptcha")
KNOWN_PROVIDERS = ("none", "test", *FUTURE_PROVIDERS)


def antibot_required() -> bool:
    raw = (os.getenv("VANGUARD_ANTIBOT_REQUIRED") or "").strip().lower()
    if raw in {"1", "true", "yes"}:
        return True
    if raw in {"0", "false", "no"}:
        return False
    return is_production_runtime()


def resolve_provider() -> str:
    return (os.getenv("VANGUARD_ANTIBOT_PROVIDER") or "none").strip().lower() or "none"


def provider_secret() -> str:
    return (
        os.getenv("VANGUARD_ANTIBOT_SECRET")
        or os.getenv("TURNSTILE_SECRET_KEY")
        or os.getenv("HCAPTCHA_SECRET")
        or os.getenv("RECAPTCHA_SECRET_KEY")
        or ""
    ).strip()


def verify_antibot(*, token: str | None, remote_ip: str | None = None) -> dict[str, Any]:
    provider = resolve_provider()
    required = antibot_required()
    token_s = (token or "").strip()

    if provider not in KNOWN_PROVIDERS:
        return _fail("unknown_provider", "Антибот провайдер не распознан.", provider, required)

    if provider in FUTURE_PROVIDERS:
        secret = provider_secret()
        if not secret:
            if required:
                return _fail(
                    "anti_bot_not_configured",
                    "Антибот обязателен, но секрет провайдера не задан.",
                    provider,
                    required,
                )
            return {
                "ok": True,
                "provider": provider,
                "captcha_active": False,
                "status": "skipped_secret_missing",
                "message_ru": "Антибот-адаптер подготовлен, провайдер не подключён.",
            }
        if required:
            return _fail(
                "anti_bot_adapter_not_wired",
                "Коммерческий CAPTCHA-адаптер ещё не подключён.",
                provider,
                required,
            )
        return {
            "ok": True,
            "provider": provider,
            "captcha_active": False,
            "status": "skipped_adapter_not_wired",
            "message_ru": "CAPTCHA не активна: адаптер не подключён.",
        }

    if provider == "test":
        if is_production_runtime():
            return _fail(
                "anti_bot_not_configured",
                "Тестовый антибот запрещён в production.",
                provider,
                required,
            )
        if token_s == TEST_TOKEN:
            return {
                "ok": True,
                "provider": "test",
                "captcha_active": False,
                "status": "test_pass",
                "message_ru": "Тестовый антибот: пройден.",
            }
        return _fail("anti_bot_rejected", "Тестовый антибот: токен отклонён.", provider, required)

    # provider == none
    if required:
        return _fail(
            "anti_bot_not_configured",
            "Антибот обязателен, но провайдер не настроен (VANGUARD_ANTIBOT_PROVIDER).",
            "none",
            required,
        )
    return {
        "ok": True,
        "provider": "none",
        "captcha_active": False,
        "status": "skipped_not_configured",
        "message_ru": "CAPTCHA не активна: провайдер не подключён.",
    }


def _fail(error: str, message_ru: str, provider: str, required: bool, *, captcha_active: bool = False) -> dict[str, Any]:
    return {
        "ok": False,
        "error": error,
        "message_ru": message_ru,
        "provider": provider,
        "captcha_active": captcha_active,
        "required": required,
        "status": "rejected",
    }
