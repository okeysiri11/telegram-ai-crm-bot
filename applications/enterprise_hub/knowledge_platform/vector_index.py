"""Vector index — store embeddings with metadata and source links."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.knowledge_platform.embedding_manager import EmbeddingManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class VectorIndex:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.embeddings = EmbeddingManager(self.store)

    def index_chunk(
        self,
        *,
        chunk_id: str,
        document_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        emb = self.embeddings.embed(text=text, ref_id=chunk_id, ref_type="chunk")
        vid = _id("ekp_vec")
        return self.store.ekp_vectors.save(
            vid,
            {
                "vector_id": vid,
                "chunk_id": chunk_id,
                "document_id": document_id,
                "embedding_id": emb["embedding_id"],
                "vector": emb["vector"],
                "text": text,
                "metadata": metadata or {},
                "indexed_at": _now(),
            },
        )

    def all(self) -> list[dict[str, Any]]:
        return self.store.ekp_vectors.list_all()

    def status(self) -> dict[str, Any]:
        return {"vectors": self.store.ekp_vectors.count()}
