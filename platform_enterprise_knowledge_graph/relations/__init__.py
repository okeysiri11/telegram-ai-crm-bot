"""Semantic Relations — Sprint 24.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_knowledge_graph.models import RELATION_TYPES


class SemanticRelations:
    def __init__(self) -> None:
        self._edges: list[dict[str, Any]] = []

    def link(
        self,
        *,
        source_id: str,
        relation: str,
        target_id: str,
        weight: float = 1.0,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        relation = (relation or "").lower()
        if relation not in RELATION_TYPES:
            raise ValueError(f"unsupported relation: {relation}")
        if not source_id or not target_id:
            raise ValueError("source_id and target_id are required")
        edge = {
            "source_id": source_id,
            "relation": relation,
            "target_id": target_id,
            "weight": float(weight),
            "meta": dict(meta or {}),
            "archived": False,
        }
        self._edges.append(edge)
        return dict(edge)

    def neighbors(self, entity_id: str, *, relation: str | None = None) -> list[dict[str, Any]]:
        edges = [dict(e) for e in self._edges if not e.get("archived") and (e["source_id"] == entity_id or e["target_id"] == entity_id)]
        if relation:
            edges = [e for e in edges if e["relation"] == relation.lower()]
        return edges

    def archive_edge(self, *, source_id: str, relation: str, target_id: str) -> dict[str, Any]:
        for e in self._edges:
            if e["source_id"] == source_id and e["relation"] == relation and e["target_id"] == target_id:
                e["archived"] = True
                return dict(e)
        raise ValueError("edge not found")

    def strengthen(self, *, source_id: str, relation: str, target_id: str, delta: float = 0.1) -> dict[str, Any]:
        for e in self._edges:
            if e["source_id"] == source_id and e["relation"] == relation and e["target_id"] == target_id and not e.get("archived"):
                e["weight"] = float(e.get("weight", 1.0)) + float(delta)
                return dict(e)
        raise ValueError("edge not found")

    def all_edges(self, *, include_archived: bool = False) -> list[dict[str, Any]]:
        if include_archived:
            return [dict(e) for e in self._edges]
        return [dict(e) for e in self._edges if not e.get("archived")]
