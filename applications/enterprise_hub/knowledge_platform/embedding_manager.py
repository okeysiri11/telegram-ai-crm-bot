"""Embedding manager — generate deterministic pseudo-embeddings."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _embed(text: str, dims: int = 16) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vals = []
    for i in range(dims):
        vals.append(((digest[i % len(digest)] / 255.0) * 2) - 1)
    return vals


class EmbeddingManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def embed(self, *, text: str, ref_id: str, ref_type: str = "chunk") -> dict[str, Any]:
        if not text:
            raise ValidationError("text is required")
        eid = _id("ekp_emb")
        vector = _embed(text)
        return self.store.ekp_embeddings.save(
            eid,
            {
                "embedding_id": eid,
                "ref_id": ref_id,
                "ref_type": ref_type,
                "dims": len(vector),
                "vector": vector,
                "at": _now(),
            },
        )

    def cosine(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
