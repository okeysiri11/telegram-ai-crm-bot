# Knowledge graph — shared knowledge, semantic search, relationships.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.assistant.events import KnowledgeUpdatedEvent
from ecosystem.assistant.models import KnowledgeEdge, KnowledgeNode
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class KnowledgeGraph:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store
        self._index: dict[str, set[str]] = {}

    async def upsert_node(
        self,
        label: str,
        content: str,
        *,
        node_type: str = "concept",
        application_id: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeNode:
        if not label:
            raise ValidationError("label is required")
        existing = next(
            (n for n in self._store.knowledge_nodes.list_all() if n.label.lower() == label.lower() and n.application_id == application_id),
            None,
        )
        if existing:
            existing.content = content
            existing.node_type = node_type
            existing.tags = tags or existing.tags
            existing.metadata = metadata or existing.metadata
            existing.embedding_hint = f"{label} {content}".lower()
            self._store.knowledge_nodes.save(existing.node_id, existing)
            self._index_node(existing)
            await publish(KnowledgeUpdatedEvent(node_id=existing.node_id, action="updated", application_id=application_id))
            return existing

        node = KnowledgeNode(
            label=label,
            content=content,
            node_type=node_type,
            application_id=application_id,
            tags=tags or [],
            embedding_hint=f"{label} {content}".lower(),
            metadata=metadata or {},
        )
        self._store.knowledge_nodes.save(node.node_id, node)
        self._index_node(node)
        await publish(KnowledgeUpdatedEvent(node_id=node.node_id, action="created", application_id=application_id))
        return node

    def link(self, source_id: str, target_id: str, *, relation: str = "related_to", weight: float = 1.0) -> KnowledgeEdge:
        if not self._store.knowledge_nodes.get(source_id) or not self._store.knowledge_nodes.get(target_id):
            raise NotFoundError("KnowledgeNode", source_id if not self._store.knowledge_nodes.get(source_id) else target_id)
        edge = KnowledgeEdge(source_id=source_id, target_id=target_id, relation=relation, weight=weight)
        self._store.knowledge_edges.save(edge.edge_id, edge)
        return edge

    def semantic_search(self, query: str, *, application_id: str = "", limit: int = 10) -> list[dict[str, Any]]:
        q = query.lower().strip()
        tokens = set(q.split())
        results: list[dict[str, Any]] = []
        for node in self._store.knowledge_nodes.list_all():
            if application_id and node.application_id not in ("", application_id):
                continue
            score = 0.0
            hint = node.embedding_hint or f"{node.label} {node.content}".lower()
            if q in hint:
                score += 2.0
            score += sum(0.5 for t in tokens if t in hint)
            score += sum(0.3 for tag in node.tags if q in tag.lower() or tag.lower() in q)
            if score > 0:
                results.append({"score": score, "node": node.to_dict()})
        return sorted(results, key=lambda r: r["score"], reverse=True)[:limit]

    def discover_relationships(self, node_id: str) -> list[dict[str, Any]]:
        node = self._store.knowledge_nodes.get(node_id)
        if node is None:
            raise NotFoundError("KnowledgeNode", node_id)
        related = []
        for edge in self._store.knowledge_edges.list_all():
            if edge.source_id == node_id:
                target = self._store.knowledge_nodes.get(edge.target_id)
                related.append({"direction": "out", "edge": edge.to_dict(), "node": target.to_dict() if target else None})
            elif edge.target_id == node_id:
                source = self._store.knowledge_nodes.get(edge.source_id)
                related.append({"direction": "in", "edge": edge.to_dict(), "node": source.to_dict() if source else None})
        return related

    async def synchronize(self, application_id: str, nodes: list[dict[str, Any]]) -> list[KnowledgeNode]:
        synced = []
        for item in nodes:
            node = await self.upsert_node(
                item.get("label", ""),
                item.get("content", ""),
                node_type=item.get("node_type", "concept"),
                application_id=application_id,
                tags=item.get("tags"),
                metadata=item.get("metadata"),
            )
            synced.append(node)
        return synced

    def get_node(self, node_id: str) -> KnowledgeNode:
        node = self._store.knowledge_nodes.get(node_id)
        if node is None:
            raise NotFoundError("KnowledgeNode", node_id)
        return node

    def list_nodes(self, *, application_id: str = "") -> list[KnowledgeNode]:
        nodes = self._store.knowledge_nodes.list_all()
        if application_id:
            return [n for n in nodes if n.application_id == application_id]
        return nodes

    def stats(self) -> dict[str, Any]:
        return {
            "nodes": self._store.knowledge_nodes.count(),
            "edges": self._store.knowledge_edges.count(),
            "indexed_tokens": len(self._index),
        }

    def _index_node(self, node: KnowledgeNode) -> None:
        tokens = set((node.embedding_hint or f"{node.label} {node.content}").lower().split())
        for token in tokens:
            self._index.setdefault(token, set()).add(node.node_id)


knowledge_graph = KnowledgeGraph()
