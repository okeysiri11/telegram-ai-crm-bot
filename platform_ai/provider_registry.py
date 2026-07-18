# Provider registry.

from __future__ import annotations

from platform_ai.exceptions import AIProviderNotFoundError
from platform_ai.provider_base import AIProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> AIProvider:
        if provider_id not in self._providers:
            raise AIProviderNotFoundError(f"Provider not found: {provider_id}")
        return self._providers[provider_id]

    def get_optional(self, provider_id: str) -> AIProvider | None:
        return self._providers.get(provider_id)

    def list_ids(self) -> list[str]:
        return list(self._providers.keys())

    def all(self) -> dict[str, AIProvider]:
        return dict(self._providers)

    def clear(self) -> None:
        self._providers.clear()


provider_registry = ProviderRegistry()
