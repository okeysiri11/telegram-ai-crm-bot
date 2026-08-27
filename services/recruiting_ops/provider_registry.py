"""Central Recruiting provider configuration registry."""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.provider_adapters import LIVE_ADAPTERS
from services.recruiting_ops.provider_connections import CONNECTION_TYPES, PROVIDERS, WIZARD_FIELDS, public_card
from services.recruiting_ops.provider_oauth import OAUTH_PROVIDERS, oauth_ready, redirect_uri
from services.recruiting_ops.secret_store import credential_presence

AUTH_TYPES = {
    "meta": "OAUTH",
    "google": "OAUTH",
    "tiktok": "OAUTH",
    "telegram": "BOT_TOKEN",
    "whatsapp": "CLOUD_API",
    "email": "SMTP",
}

HEALTH_ENDPOINTS = {
    "meta": "GET /me and ad account",
    "google": "Google Ads search customer",
    "tiktok": "GET /advertiser/info",
    "telegram": "GET /getMe",
    "whatsapp": "GET /{phone_number_id}",
    "email": "SMTP EHLO/STARTTLS",
}


def registry_entry(provider: str, row: dict[str, Any] | None = None) -> dict[str, Any]:
    key = (provider or "").strip().lower()
    adapter = LIVE_ADAPTERS[key]
    card = public_card(row or {"provider": key, "status": "NOT_CONFIGURED", "mode": "LIVE"})
    wizard = WIZARD_FIELDS.get(key) or []
    creds = credential_presence(key)
    return {
        "provider_id": key,
        "display_name": adapter.label,
        "mode": card["mode"],
        "status": card["status"],
        "auth_type": AUTH_TYPES[key],
        "required_configuration": [field["id"] for field in wizard if field.get("required")],
        "optional_configuration": [field["id"] for field in wizard if not field.get("required")],
        "capabilities": list(adapter.capabilities),
        "health_endpoint": HEALTH_ENDPOINTS[key],
        "last_health_check": card.get("last_successful_health_check"),
        "last_success": card.get("last_successful_health_check"),
        "last_error": card.get("last_error"),
        "credential_expiry": card.get("credential_expiry"),
        "account_identifier": card.get("account_id"),
        "oauth_ready": oauth_ready(key) if key in OAUTH_PROVIDERS else False,
        "redirect_uri": redirect_uri(key) if key in OAUTH_PROVIDERS else None,
        "credential_presence": creds["present"],
        "connection_type": CONNECTION_TYPES.get(key),
    }


def provider_registry(connections: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    by = {(item.get("provider") or ""): item for item in connections or []}
    items = [registry_entry(provider, by.get(provider)) for provider in PROVIDERS]
    return {"ok": True, "items": items, "fake_data": False}
