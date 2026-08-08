"""Sprint 43.2 — secure API key vault for AI providers (wraps SecretManager)."""

from __future__ import annotations

import os
from typing import Any

from platform_security.secrets.manager import SecretManager, secret_manager

# Canonical vault names — never store raw keys in modules.
PROVIDER_KEY_NAMES: dict[str, str] = {
    "openai": "ai.provider.openai.api_key",
    "anthropic": "ai.provider.anthropic.api_key",
    "google": "ai.provider.google.api_key",
    "gemini": "ai.provider.google.api_key",
    "runway": "ai.provider.runway.api_key",
    "elevenlabs": "ai.provider.elevenlabs.api_key",
    "flux": "ai.provider.flux.api_key",
    "pika": "ai.provider.pika.api_key",
    "kling": "ai.provider.kling.api_key",
    "luma": "ai.provider.luma.api_key",
    "recraft": "ai.provider.recraft.api_key",
    "ideogram": "ai.provider.ideogram.api_key",
    "stability": "ai.provider.stability.api_key",
    "bfl": "ai.provider.bfl.api_key",
    "fal": "ai.provider.fal.api_key",
    "replicate": "ai.provider.replicate.api_key",
    "cartesia": "ai.provider.cartesia.api_key",
    "azure": "ai.provider.azure.api_key",
    "deepseek": "ai.provider.deepseek.api_key",
    "mistral": "ai.provider.mistral.api_key",
    "hailuo": "ai.provider.hailuo.api_key",
    "openrouter": "ai.provider.openrouter.api_key",
}

# Env fallbacks (optional) — mapped into vault on bootstrap.
ENV_FALLBACKS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "runway": "RUNWAY_API_KEY",
    "elevenlabs": "ELEVENLABS_API_KEY",
    "flux": "FLUX_API_KEY",
    "stability": "STABILITY_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "fal": "FAL_API_KEY",
    "replicate": "REPLICATE_API_TOKEN",
}


class ProviderKeyVault:
    """Encrypted storage for provider API keys."""

    def __init__(self, secrets: SecretManager | None = None) -> None:
        self._secrets = secrets or secret_manager

    def store(self, vendor: str, value: str) -> dict[str, Any]:
        name = PROVIDER_KEY_NAMES.get(vendor.lower())
        if not name:
            raise ValueError(f"Неизвестный провайдер ключа: {vendor}")
        if not value or value.startswith("vault://"):
            raise ValueError("Требуется значение ключа (не vault-ссылка)")
        rec = self._secrets.store(name, value, metadata={"vendor": vendor.lower(), "kind": "ai_provider"})
        return {"vendor": vendor.lower(), "key_ref": name, "secret_id": rec.secret_id, "version": rec.version}

    def get(self, vendor: str) -> str | None:
        name = PROVIDER_KEY_NAMES.get(vendor.lower())
        if not name:
            return None
        try:
            return self._secrets.retrieve_by_name(name)
        except Exception:
            env = ENV_FALLBACKS.get(vendor.lower())
            if env:
                return os.environ.get(env) or None
            return None

    def has(self, vendor: str) -> bool:
        return bool(self.get(vendor))

    def list_status(self) -> list[dict[str, Any]]:
        rows = []
        for vendor, name in PROVIDER_KEY_NAMES.items():
            rows.append(
                {
                    "vendor": vendor,
                    "key_ref": name,
                    "configured": self.has(vendor),
                }
            )
        return rows

    def bootstrap_from_env(self) -> dict[str, Any]:
        loaded = []
        for vendor, env in ENV_FALLBACKS.items():
            val = os.environ.get(env)
            if val and not self.has(vendor):
                self.store(vendor, val)
                loaded.append(vendor)
        return {"loaded": loaded, "count": len(loaded)}


provider_key_vault = ProviderKeyVault()
