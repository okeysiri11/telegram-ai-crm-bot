# Platform Memory — embedding provider abstraction.

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Replaceable embedding backend (OpenAI, local, pgvector adapter, etc.)."""

    dimensions: int = 384

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    async def batch_embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _deterministic_embed(text: str, dimensions: int) -> list[float]:
    vec: list[float] = []
    for i in range(dimensions):
        digest = hashlib.sha256(f"{text}:{i}".encode()).digest()
        vec.append((int.from_bytes(digest[:4], "big") / 2**32) * 2 - 1)
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class DummyEmbeddingProvider(EmbeddingProvider):
    """Deterministic in-memory embeddings — no external API dependency."""

    dimensions = 384

    async def embed(self, text: str) -> list[float]:
        return _deterministic_embed(f"dummy:{text}", self.dimensions)

    async def batch_embed(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(text) for text in texts]
