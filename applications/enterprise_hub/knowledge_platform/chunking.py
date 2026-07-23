"""Chunking — split documents into retrieval chunks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.knowledge_platform.document_manager import DocumentManager
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ChunkingEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.documents = DocumentManager(self.store)

    def chunk(self, *, document_id: str, size: int = 200, overlap: int = 40) -> list[dict[str, Any]]:
        if size <= 0:
            raise ValidationError("size must be positive")
        doc = self.documents.get(document_id)
        text = doc.get("content") or doc.get("title") or ""
        chunks = []
        start = 0
        idx = 0
        while start < len(text) or (not text and idx == 0):
            piece = text[start : start + size] if text else doc.get("title", "")
            cid = _id("ekp_chk")
            record = self.store.ekp_chunks.save(
                cid,
                {
                    "chunk_id": cid,
                    "document_id": document_id,
                    "index": idx,
                    "text": piece,
                    "start": start,
                    "end": start + len(piece),
                    "at": _now(),
                },
            )
            chunks.append(record)
            idx += 1
            if not text:
                break
            start = start + size - overlap
            if start >= len(text):
                break
        return chunks
