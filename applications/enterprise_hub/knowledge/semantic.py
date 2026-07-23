"""Semantic intelligence — search, resolution, duplicates, inference, similarity."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SemanticIntelligence:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.semantic_ops = list(DEFAULT_CONFIG.kg_semantic_ops)

    def operate(
        self,
        *,
        operation: str,
        query: str,
        score: float = 0.8,
        results: list[str] | None = None,
        detail: str = "",
    ) -> dict[str, Any]:
        op = operation.lower().strip()
        if op not in self.semantic_ops:
            raise ValidationError(f"operation must be one of {self.semantic_ops}")
        if not query:
            raise ValidationError("query required")
        sid = _id("kg_sem")
        matches = results or [
            e["entity_id"]
            for e in self.store.kg_entities.list_all()
            if query.lower() in e["name"].lower()
        ][:10]
        return self.store.kg_semantics.save(
            sid,
            {
                "semantic_id": sid,
                "operation": op,
                "query": query,
                "score": max(0.0, min(1.0, float(score))),
                "results": matches,
                "detail": detail or f"{op} for '{query}'",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "operations": self.store.kg_semantics.count(),
            "types": self.semantic_ops,
        }
