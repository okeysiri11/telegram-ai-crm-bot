# Prompt cache — identical prompts with configurable TTL.

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from platform_ai.models import AIResponse


class AICache:
    def __init__(self, *, default_ttl: float = 3600.0) -> None:
        self._store: dict[str, tuple[float, AIResponse]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def reset(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0

    def _key(self, provider_id: str, model_id: str, prompt: str, context: dict[str, Any]) -> str:
        payload = json.dumps({"p": provider_id, "m": model_id, "prompt": prompt, "ctx": context}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(
        self,
        provider_id: str,
        model_id: str,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> AIResponse | None:
        key = self._key(provider_id, model_id, prompt, context or {})
        entry = self._store.get(key)
        if not entry:
            self.misses += 1
            return None
        expires_at, response = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            self.misses += 1
            return None
        self.hits += 1
        cached = AIResponse(
            request_id=response.request_id,
            provider_id=response.provider_id,
            model_id=response.model_id,
            content=response.content,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost_usd=response.cost_usd,
            latency_ms=0.0,
            cached=True,
            metadata=response.metadata,
        )
        return cached

    def set(
        self,
        provider_id: str,
        model_id: str,
        prompt: str,
        response: AIResponse,
        context: dict[str, Any] | None = None,
        ttl: float | None = None,
    ) -> None:
        key = self._key(provider_id, model_id, prompt, context or {})
        expires = time.monotonic() + (ttl if ttl is not None else self.default_ttl)
        self._store[key] = (expires, response)

    def invalidate(self, provider_id: str | None = None, model_id: str | None = None) -> int:
        removed = 0
        keys = list(self._store.keys())
        for key in keys:
            _, response = self._store[key]
            if provider_id and response.provider_id != provider_id:
                continue
            if model_id and response.model_id != model_id:
                continue
            del self._store[key]
            removed += 1
        return removed

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "entries": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total else 0.0,
            "default_ttl": self.default_ttl,
        }


ai_cache = AICache()
