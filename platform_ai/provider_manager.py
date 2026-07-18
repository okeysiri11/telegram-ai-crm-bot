# Provider manager — lifecycle, health, configuration.

from __future__ import annotations

import logging
from typing import Any

from platform_ai.model_registry import model_registry
from platform_ai.models import AIProviderRecord, ProviderStatus
from platform_ai.provider_base import AIProvider, MockAIProvider
from platform_ai.provider_registry import provider_registry

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER_CONFIG: dict[str, dict[str, Any]] = {
    "openai": {"api_base": "https://api.openai.com/v1", "default_model": "gpt-4o-mini"},
    "anthropic": {"api_base": "https://api.anthropic.com", "default_model": "claude-3-haiku"},
    "google": {"api_base": "https://generativelanguage.googleapis.com", "default_model": "gemini-1.5-flash"},
    "openrouter": {"api_base": "https://openrouter.ai/api/v1", "default_model": "openai/gpt-4o-mini"},
    "local_llama": {"api_base": "http://localhost:11434", "default_model": "llama-3.1-8b"},
    "deepseek": {"api_base": "https://api.deepseek.com", "default_model": "deepseek-chat"},
}


class ProviderManager:
    def __init__(self) -> None:
        self._enabled: dict[str, bool] = {}
        self._default_provider = "openrouter"
        self._fallback_chain = ["openrouter", "openai", "anthropic", "google", "deepseek", "local_llama"]
        self._initialized = False

    def reset(self) -> None:
        provider_registry.clear()
        model_registry.clear()
        self._enabled.clear()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        model_registry.load_defaults()
        self._register_builtin_providers()
        self._initialized = True
        logger.info("ai_platform_initialized providers=%s models=%s", len(provider_registry.all()), len(model_registry.list_all()))

    def _register_builtin_providers(self) -> None:
        providers = [
            MockAIProvider("openai", "OpenAI", response_prefix="[openai]"),
            MockAIProvider("anthropic", "Anthropic Claude", response_prefix="[claude]"),
            MockAIProvider("google", "Google Gemini", response_prefix="[gemini]"),
            MockAIProvider("openrouter", "OpenRouter", response_prefix="[openrouter]"),
            MockAIProvider("local_llama", "Local Llama", response_prefix="[llama]", latency_ms=200.0),
            MockAIProvider("deepseek", "DeepSeek", response_prefix="[deepseek]"),
        ]
        for provider in providers:
            provider.config = DEFAULT_PROVIDER_CONFIG.get(provider.provider_id, {})
            provider_registry.register(provider)
            self._enabled[provider.provider_id] = True

    def set_default_provider(self, provider_id: str) -> None:
        self._default_provider = provider_id

    def set_fallback_chain(self, chain: list[str]) -> None:
        self._fallback_chain = chain

    def enable(self, provider_id: str) -> None:
        self._enabled[provider_id] = True

    def disable(self, provider_id: str) -> None:
        self._enabled[provider_id] = False

    def is_enabled(self, provider_id: str) -> bool:
        return self._enabled.get(provider_id, False)

    @property
    def default_provider(self) -> str:
        return self._default_provider

    @property
    def fallback_chain(self) -> list[str]:
        return list(self._fallback_chain)

    async def health_all(self) -> list[AIProviderRecord]:
        records: list[AIProviderRecord] = []
        for provider_id, provider in provider_registry.all().items():
            status = await provider.health_check()
            models = [m.model_id for m in model_registry.list_by_provider(provider_id)]
            records.append(
                AIProviderRecord(
                    provider_id=provider_id,
                    name=provider.name,
                    enabled=self.is_enabled(provider_id),
                    status=status,
                    latency_ms=provider.average_latency_ms,
                    models=models,
                    config=provider.config,
                )
            )
        return records

    async def health(self, provider_id: str) -> AIProviderRecord:
        provider = provider_registry.get(provider_id)
        status = await provider.health_check()
        models = [m.model_id for m in model_registry.list_by_provider(provider_id)]
        return AIProviderRecord(
            provider_id=provider_id,
            name=provider.name,
            enabled=self.is_enabled(provider_id),
            status=status,
            latency_ms=provider.average_latency_ms,
            models=models,
            config=provider.config,
        )

    def get_provider(self, provider_id: str) -> AIProvider:
        if not self.is_enabled(provider_id):
            from platform_ai.exceptions import AIProviderUnavailableError

            raise AIProviderUnavailableError(f"Provider disabled: {provider_id}")
        return provider_registry.get(provider_id)


provider_manager = ProviderManager()
