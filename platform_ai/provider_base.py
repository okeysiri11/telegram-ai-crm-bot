# Abstract AI provider — all LLM integrations implement this.

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from platform_ai.models import AIMessage, AIRequest, ProviderStatus


class ProviderResponse:
    def __init__(
        self,
        content: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.content = content
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.metadata = metadata or {}


class AIProvider(ABC):
    """Provider-agnostic interface — Platform Core never calls LLMs directly."""

    provider_id: str = ""
    name: str = ""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = dict(config or {})
        self._latency_samples: list[float] = []
        self._failure_count = 0

    @abstractmethod
    async def complete(self, request: AIRequest, *, model_id: str) -> ProviderResponse:
        """Execute completion against the provider."""

    async def health_check(self) -> ProviderStatus:
        if self._failure_count >= 3:
            return ProviderStatus.UNAVAILABLE
        if self._failure_count >= 1:
            return ProviderStatus.DEGRADED
        return ProviderStatus.AVAILABLE

    @property
    def average_latency_ms(self) -> float:
        if not self._latency_samples:
            return 0.0
        return sum(self._latency_samples[-20:]) / len(self._latency_samples[-20:])

    def record_success(self, latency_ms: float) -> None:
        self._latency_samples.append(latency_ms)
        self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self) -> None:
        self._failure_count += 1

    def _messages_to_prompt(self, request: AIRequest) -> str:
        if request.prompt:
            return request.prompt
        return "\n".join(f"{m.role}: {m.content}" for m in request.messages)

    async def _timed_complete(self, request: AIRequest, *, model_id: str) -> ProviderResponse:
        start = time.monotonic()
        try:
            result = await self.complete(request, model_id=model_id)
            self.record_success((time.monotonic() - start) * 1000)
            return result
        except Exception:
            self.record_failure()
            raise


class MockAIProvider(AIProvider):
    """Deterministic mock provider for testing and offline development."""

    def __init__(
        self,
        provider_id: str,
        name: str,
        *,
        response_prefix: str = "[mock]",
        latency_ms: float = 50.0,
        fail: bool = False,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(config)
        self.provider_id = provider_id
        self.name = name
        self.response_prefix = response_prefix
        self.simulated_latency_ms = latency_ms
        self.fail = fail

    async def complete(self, request: AIRequest, *, model_id: str) -> ProviderResponse:
        import asyncio

        await asyncio.sleep(self.simulated_latency_ms / 1000)
        if self.fail:
            raise RuntimeError(f"Mock provider {self.provider_id} simulated failure")

        prompt = self._messages_to_prompt(request)
        content = f"{self.response_prefix} ({self.provider_id}/{model_id}): {prompt[:200]}"
        tokens_in = max(1, len(prompt) // 4)
        tokens_out = max(1, len(content) // 4)
        return ProviderResponse(content=content, tokens_in=tokens_in, tokens_out=tokens_out)
