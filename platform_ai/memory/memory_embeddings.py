# Embedding provider abstraction — OpenAI, local, future providers.

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from typing import Any


class EmbeddingProvider(ABC):
    provider_id: str = ""
    dimensions: int = 384

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...


def _hash_embed(text: str, dimensions: int) -> list[float]:
    """Deterministic mock embedding from text hash."""
    vec = []
    for i in range(dimensions):
        h = hashlib.sha256(f"{text}:{i}".encode()).digest()
        vec.append((int.from_bytes(h[:4], "big") / 2**32) * 2 - 1)
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    provider_id = "openai"
    dimensions = 1536

    async def embed(self, text: str) -> list[float]:
        return _hash_embed(f"openai:{text}", self.dimensions)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


class LocalEmbeddingProvider(EmbeddingProvider):
    provider_id = "local"
    dimensions = 384

    async def embed(self, text: str) -> list[float]:
        return _hash_embed(f"local:{text}", self.dimensions)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


class EmbeddingRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, EmbeddingProvider] = {
            "openai": OpenAIEmbeddingProvider(),
            "local": LocalEmbeddingProvider(),
        }
        self._default = "local"

    def reset(self) -> None:
        self._providers = {
            "openai": OpenAIEmbeddingProvider(),
            "local": LocalEmbeddingProvider(),
        }
        self._default = "local"

    def get(self, provider_id: str | None = None) -> EmbeddingProvider:
        pid = provider_id or self._default
        if pid not in self._providers:
            from platform_ai.memory.exceptions import EmbeddingError

            raise EmbeddingError(f"Unknown embedding provider: {pid}")
        return self._providers[provider_id or self._default]

    def set_default(self, provider_id: str) -> None:
        self._default = provider_id

    def list_providers(self) -> list[dict[str, Any]]:
        return [{"provider_id": p.provider_id, "dimensions": p.dimensions} for p in self._providers.values()]


embedding_registry = EmbeddingRegistry()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
