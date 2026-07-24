"""Documentation registry — Sprint 21.6."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from platform_documentation.models import DOC_CATEGORIES, DOC_CHANNELS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DocumentationRegistry:
    def __init__(self) -> None:
        self._docs: dict[str, dict[str, Any]] = {}

    def register(
        self,
        *,
        title: str,
        category: str,
        content: str = "",
        version: str = "6.0.0-rc6",
        channel: str = "release_candidate",
        module: str | None = None,
        kind: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if category not in DOC_CATEGORIES:
            raise ValueError(f"invalid category: {category}")
        if channel not in DOC_CHANNELS:
            raise ValueError(f"invalid channel: {channel}")
        if not title:
            raise ValueError("title is required")
        did = f"doc_{uuid.uuid4().hex[:12]}"
        record = {
            "doc_id": did,
            "title": title,
            "category": category,
            "content": content,
            "version": version,
            "channel": channel,
            "module": module,
            "kind": kind or category,
            "metadata": metadata or {},
            "registered_at": _now(),
        }
        self._docs[did] = record
        return record

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._docs.values())

    def by_category(self) -> dict[str, int]:
        counts = {c: 0 for c in DOC_CATEGORIES}
        for doc in self._docs.values():
            counts[doc["category"]] = counts.get(doc["category"], 0) + 1
        return counts

    def status(self) -> dict[str, Any]:
        return {"docs": len(self._docs), "by_category": self.by_category()}
