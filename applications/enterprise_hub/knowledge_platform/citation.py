"""Citation — attach source references to answers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CitationEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def cite(self, *, answer_id: str, hits: list[dict[str, Any]]) -> dict[str, Any]:
        sources = []
        for h in hits:
            doc = self.store.ekp_documents.get(h.get("document_id", ""))
            sources.append(
                {
                    "document_id": h.get("document_id"),
                    "chunk_id": h.get("chunk_id"),
                    "title": (doc or {}).get("title"),
                    "score": h.get("score"),
                    "excerpt": (h.get("text") or "")[:120],
                }
            )
        cid = _id("ekp_cit")
        return self.store.ekp_citations.save(
            cid,
            {"citation_id": cid, "answer_id": answer_id, "sources": sources, "at": _now()},
        )
