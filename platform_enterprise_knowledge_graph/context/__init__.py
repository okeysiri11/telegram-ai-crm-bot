"""Context Engine — Sprint 24.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_knowledge_graph.models import CONTEXT_SOURCES


class ContextEngine:
    def build(
        self,
        *,
        task: str,
        entity_ids: list[str] | None = None,
        sources: list[str] | None = None,
        related: list[dict[str, Any]] | None = None,
        memory: list[dict[str, Any]] | None = None,
        elapsed_ms: float = 2.0,
    ) -> dict[str, Any]:
        if not task:
            raise ValueError("task is required")
        sources = list(sources or CONTEXT_SOURCES)
        for s in sources:
            if s not in CONTEXT_SOURCES:
                raise ValueError(f"unsupported context source: {s}")
        return {
            "task": task.strip(),
            "entity_ids": list(entity_ids or []),
            "sources": sources,
            "related_objects": list(related or []),
            "memory_snippets": list(memory or []),
            "elapsed_ms": float(elapsed_ms),
            "context_in_milliseconds": float(elapsed_ms) < 1000,
            "full_context": True,
        }
