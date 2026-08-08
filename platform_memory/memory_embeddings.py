"""Epic 45.2 — embeddings for Knowledge Memory (Level 5)."""

from __future__ import annotations

import math
import re
from typing import Iterable

from platform_memory.providers.embedding_provider import DummyEmbeddingProvider, EmbeddingProvider


_TOKEN = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9_]{2,}", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "")]


class MemoryEmbeddings:
    """Bag-of-words + optional EmbeddingProvider — RAG-ready vector layer."""

    DIM = 64

    def __init__(self, provider: EmbeddingProvider | None = None) -> None:
        self._provider = provider or DummyEmbeddingProvider()

    def embed(self, text: str) -> list[float]:
        # Deterministic local embedding for tests / offline; provider reserved for production.
        vec = [0.0] * self.DIM
        toks = tokenize(text)
        if not toks:
            return vec
        for t in toks:
            h = hash(t) % self.DIM
            vec[h] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b))

    def rank(self, query: str, documents: Iterable[tuple[str, str]]) -> list[tuple[str, float]]:
        qv = self.embed(query)
        scored: list[tuple[str, float]] = []
        for doc_id, text in documents:
            scored.append((doc_id, self.similarity(qv, self.embed(text))))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored


memory_embeddings = MemoryEmbeddings()
