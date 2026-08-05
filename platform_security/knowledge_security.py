# Knowledge / RAG / embeddings security — Sprint 32.4.

from __future__ import annotations

from typing import Any


class KnowledgeSecurity:
    """Protect knowledge base, RAG, embeddings, documents, semantic search, context windows."""

    SENSITIVITY = ("public", "internal", "confidential", "restricted")

    def classify_document(self, *, doc_id: str, sensitivity: str = "internal") -> dict[str, Any]:
        level = sensitivity if sensitivity in self.SENSITIVITY else "internal"
        return {
            "doc_id": doc_id,
            "sensitivity": level,
            "encryption_required": level in {"confidential", "restricted"},
            "tenant_scoped": True,
        }

    def authorize_retrieval(
        self,
        *,
        tenant_id: str | None,
        sensitivity: str,
        principal_clearance: str = "internal",
    ) -> dict[str, Any]:
        if not tenant_id:
            return {"ok": False, "reason": "tenant_required"}
        order = {s: i for i, s in enumerate(self.SENSITIVITY)}
        if order.get(sensitivity, 1) > order.get(principal_clearance, 1):
            return {"ok": False, "reason": "clearance_insufficient", "sensitivity": sensitivity}
        return {"ok": True, "tenant_id": tenant_id, "sensitivity": sensitivity}

    def guard_context_window(self, texts: list[str], *, max_chars: int = 12000) -> dict[str, Any]:
        joined = "\n".join(texts)
        truncated = joined[:max_chars]
        return {
            "ok": True,
            "chars": len(truncated),
            "truncated": len(joined) > max_chars,
            "policy": "context_window_limit",
        }

    def guard_embedding_query(self, query: str, *, tenant_id: str | None) -> dict[str, Any]:
        if not tenant_id:
            return {"ok": False, "reason": "tenant_required_for_vector_search"}
        if len(query or "") > 4000:
            return {"ok": False, "reason": "query_too_long"}
        return {"ok": True, "tenant_id": tenant_id, "vector_scoped": True}

    def capabilities(self) -> dict[str, Any]:
        return {
            "knowledge_base": True,
            "rag": True,
            "embeddings": True,
            "vector_database": True,
            "documents": True,
            "semantic_search": True,
            "context_windows": True,
            "tenant_isolation": True,
            "sensitivity_levels": list(self.SENSITIVITY),
        }
