"""Project Memory Engine — registry, layers, semantic search, relations.

Sprint 36.5 — extends platform_memory SoR (reuses DummyEmbeddingProvider).
"""

from __future__ import annotations

import time
from typing import Any

from platform_memory.project_memory_models import (
    MemoryChunk,
    MemoryEmbedding,
    MemoryFeedback,
    MemoryHistoryEntry,
    MemoryKind,
    MemoryLayer,
    MemoryRecord,
    MemoryRelation,
    MemorySearchHit,
    MemorySession,
    new_id,
)
from platform_memory.providers.embedding_provider import (
    DummyEmbeddingProvider,
    EmbeddingProvider,
    cosine_similarity,
)

LAYER_DEFAULT_TTL = {
    MemoryLayer.SHORT_TERM: 3600.0,
    MemoryLayer.WORKING: 86400.0,
    MemoryLayer.LONG_TERM: None,
    MemoryLayer.SHARED_TEAM: None,
}


class ProjectMemoryEngine:
    def __init__(self, *, embedding: EmbeddingProvider | None = None) -> None:
        self.embedding = embedding or DummyEmbeddingProvider()
        self.memories: dict[str, MemoryRecord] = {}
        self.chunks: dict[str, list[MemoryChunk]] = {}
        self.embeddings: dict[str, MemoryEmbedding] = {}
        self.relations: list[MemoryRelation] = []
        self.sessions: dict[str, MemorySession] = {}
        self.history: list[MemoryHistoryEntry] = []
        self.feedback: list[MemoryFeedback] = []
        self._seeded = False

    def reset(self) -> None:
        self.memories.clear()
        self.chunks.clear()
        self.embeddings.clear()
        self.relations.clear()
        self.sessions.clear()
        self.history.clear()
        self.feedback.clear()
        self._seeded = False

    def _log(self, action: str, *, memory_id: str | None = None, session_id: str | None = None, details: dict | None = None) -> None:
        self.history.append(
            MemoryHistoryEntry(
                history_id=new_id("mh"),
                action=action,
                memory_id=memory_id,
                session_id=session_id,
                details=details or {},
            )
        )
        self.history = self.history[-5000:]

    def ensure_seed(self) -> None:
        if self._seeded:
            return
        seeds = [
            {
                "kind": MemoryKind.PROJECT,
                "layer": MemoryLayer.LONG_TERM,
                "title": "Sprint 36.5 goals",
                "content": "Build Project Memory Engine with semantic search and memory layers.",
                "project_id": "proj_ados",
                "tags": ["sprint", "memory"],
                "importance": 0.9,
            },
            {
                "kind": MemoryKind.AGENT,
                "layer": MemoryLayer.WORKING,
                "title": "Orchestrator preference",
                "content": "Prefer extending platform_memory over creating a second memory package.",
                "agent_id": "agent_orchestrator",
                "project_id": "proj_ados",
                "importance": 0.85,
            },
            {
                "kind": MemoryKind.CLIENT,
                "layer": MemoryLayer.LONG_TERM,
                "title": "Client preference",
                "content": "Enterprise client prefers concise Russian/English bilingual replies.",
                "client_id": "client_demo",
                "importance": 0.7,
            },
            {
                "kind": MemoryKind.WORKFLOW,
                "layer": MemoryLayer.SHORT_TERM,
                "title": "Approval pipeline state",
                "content": "Workflow wf_approval_pipeline last run approved amount=1000.",
                "workflow_id": "wf_approval_pipeline",
                "project_id": "proj_ados",
                "importance": 0.6,
            },
            {
                "kind": MemoryKind.DOCUMENT,
                "layer": MemoryLayer.SHARED_TEAM,
                "title": "Architecture note",
                "content": "Project Memory Engine lives inside platform_memory SoR — no platform_project_memory package.",
                "document_id": "doc_arch_pm",
                "project_id": "proj_ados",
                "tags": ["architecture", "docs"],
                "importance": 0.8,
            },
        ]
        for item in seeds:
            self.remember(item, embed=False)
        # relation graph
        ids = list(self.memories.keys())
        if len(ids) >= 2:
            self.link(ids[0], ids[1], relation="supports", weight=0.9)
            self.link(ids[1], ids[4] if len(ids) > 4 else ids[0], relation="references", weight=0.7)
        self._seeded = True

    def _chunk_text(self, memory_id: str, content: str, *, size: int = 240) -> list[MemoryChunk]:
        parts = [content[i : i + size] for i in range(0, max(len(content), 1), size)] or [content]
        chunks = [
            MemoryChunk(
                chunk_id=new_id("mchk"),
                memory_id=memory_id,
                ordinal=i,
                text=part,
                tokens=max(1, len(part) // 4),
            )
            for i, part in enumerate(parts)
        ]
        self.chunks[memory_id] = chunks
        return chunks

    async def _embed_memory(self, record: MemoryRecord) -> MemoryEmbedding:
        chunks = self.chunks.get(record.memory_id) or self._chunk_text(record.memory_id, record.content)
        text = " ".join(c.text for c in chunks)
        vector = await self.embedding.embed(text)
        emb = MemoryEmbedding(
            embedding_id=new_id("memb"),
            memory_id=record.memory_id,
            chunk_id=chunks[0].chunk_id if chunks else None,
            dims=len(vector),
            vector=vector,
            model=getattr(self.embedding, "__class__", type(self.embedding)).__name__,
        )
        self.embeddings[record.memory_id] = emb
        return emb

    def remember(self, body: dict[str, Any], *, embed: bool = True) -> MemoryRecord:
        kind = MemoryKind(body.get("kind") or MemoryKind.PROJECT.value)
        layer = MemoryLayer(body.get("layer") or MemoryLayer.LONG_TERM.value)
        ttl = body.get("expires_at")
        if ttl is None and LAYER_DEFAULT_TTL.get(layer):
            ttl = time.time() + float(LAYER_DEFAULT_TTL[layer])
        memory_id = str(body.get("memory_id") or new_id("pmem"))
        record = MemoryRecord(
            memory_id=memory_id,
            kind=kind,
            layer=layer,
            title=str(body.get("title") or ""),
            content=str(body.get("content") or body.get("text") or ""),
            project_id=body.get("project_id"),
            agent_id=body.get("agent_id"),
            client_id=body.get("client_id"),
            workflow_id=body.get("workflow_id"),
            document_id=body.get("document_id"),
            tags=list(body.get("tags") or []),
            importance=float(body.get("importance") or 0.5),
            metadata=dict(body.get("metadata") or {}),
            expires_at=ttl,
        )
        self.memories[memory_id] = record
        self._chunk_text(memory_id, record.content)
        self._log("remember", memory_id=memory_id, details={"kind": kind.value, "layer": layer.value})
        if embed:
            # sync embed via cached dummy path using deterministic helper
            import asyncio

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(self._embed_memory(record))
            else:
                loop.create_task(self._embed_memory(record))
        return record

    async def remember_async(self, body: dict[str, Any]) -> MemoryRecord:
        record = self.remember(body, embed=False)
        await self._embed_memory(record)
        return record

    def get(self, memory_id: str) -> MemoryRecord:
        rec = self.memories.get(memory_id)
        if rec is None:
            raise KeyError(f"memory not found: {memory_id}")
        return rec

    def list_memories(
        self,
        *,
        kind: str | None = None,
        layer: str | None = None,
        project_id: str | None = None,
        agent_id: str | None = None,
        include_expired: bool = False,
    ) -> list[MemoryRecord]:
        now = time.time()
        rows = list(self.memories.values())
        if not include_expired:
            rows = [r for r in rows if r.expires_at is None or r.expires_at >= now]
        if kind:
            rows = [r for r in rows if (r.kind.value if isinstance(r.kind, MemoryKind) else r.kind) == kind]
        if layer:
            rows = [r for r in rows if (r.layer.value if isinstance(r.layer, MemoryLayer) else r.layer) == layer]
        if project_id:
            rows = [r for r in rows if r.project_id == project_id]
        if agent_id:
            rows = [r for r in rows if r.agent_id == agent_id]
        return sorted(rows, key=lambda r: r.updated_at, reverse=True)

    def forget(self, memory_id: str) -> bool:
        existed = self.memories.pop(memory_id, None) is not None
        self.chunks.pop(memory_id, None)
        self.embeddings.pop(memory_id, None)
        if existed:
            self._log("forget", memory_id=memory_id)
        return existed

    def link(self, from_id: str, to_id: str, *, relation: str = "related", weight: float = 1.0) -> MemoryRelation:
        rel = MemoryRelation(
            relation_id=new_id("mrel"),
            from_id=from_id,
            to_id=to_id,
            relation=relation,
            weight=weight,
        )
        self.relations.append(rel)
        self._log("link", details={"from": from_id, "to": to_id, "relation": relation})
        return rel

    def relations_graph(self, *, project_id: str | None = None) -> dict[str, Any]:
        mems = self.list_memories(project_id=project_id, include_expired=True)
        ids = {m.memory_id for m in mems}
        nodes = [
            {
                "id": m.memory_id,
                "label": m.title or m.memory_id,
                "kind": m.kind.value if isinstance(m.kind, MemoryKind) else m.kind,
                "layer": m.layer.value if isinstance(m.layer, MemoryLayer) else m.layer,
            }
            for m in mems
        ]
        edges = [
            r.to_dict()
            for r in self.relations
            if (not ids or (r.from_id in ids and r.to_id in ids))
        ]
        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}

    async def search(
        self,
        query: str,
        *,
        kind: str | None = None,
        layer: str | None = None,
        project_id: str | None = None,
        limit: int = 10,
        min_score: float = 0.05,
    ) -> list[MemorySearchHit]:
        self.ensure_seed()
        qvec = await self.embedding.embed(query)
        qlow = query.lower().strip()
        hits: list[MemorySearchHit] = []
        for rec in self.list_memories(kind=kind, layer=layer, project_id=project_id):
            emb = self.embeddings.get(rec.memory_id)
            if emb is None:
                emb = await self._embed_memory(rec)
            sim = cosine_similarity(qvec, emb.vector)
            kw = 0.25 if qlow and qlow in (rec.content + " " + rec.title).lower() else 0.0
            score = sim * 0.75 + kw + float(rec.importance) * 0.1
            if score < min_score:
                continue
            hits.append(
                MemorySearchHit(
                    memory_id=rec.memory_id,
                    score=round(score, 4),
                    kind=rec.kind.value if isinstance(rec.kind, MemoryKind) else str(rec.kind),
                    layer=rec.layer.value if isinstance(rec.layer, MemoryLayer) else str(rec.layer),
                    title=rec.title,
                    content=rec.content,
                    snippet=rec.content[:160],
                )
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]

    def create_session(self, body: dict[str, Any] | None = None) -> MemorySession:
        body = body or {}
        session = MemorySession(
            session_id=new_id("msess"),
            project_id=body.get("project_id"),
            agent_id=body.get("agent_id"),
            working_set=list(body.get("working_set") or []),
            metadata=dict(body.get("metadata") or {}),
        )
        self.sessions[session.session_id] = session
        self._log("session_created", session_id=session.session_id)
        return session

    def get_session(self, session_id: str) -> MemorySession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"memory session not found: {session_id}")
        return session

    def list_sessions(self) -> list[MemorySession]:
        return sorted(self.sessions.values(), key=lambda s: s.created_at, reverse=True)

    def pin_to_session(self, session_id: str, memory_id: str) -> MemorySession:
        session = self.get_session(session_id)
        self.get(memory_id)
        if memory_id not in session.working_set:
            session.working_set.append(memory_id)
        session.updated_at = time.time()
        self._log("session_pin", session_id=session_id, memory_id=memory_id)
        return session

    def add_feedback(self, body: dict[str, Any]) -> MemoryFeedback:
        memory_id = str(body.get("memory_id") or "")
        self.get(memory_id)
        fb = MemoryFeedback(
            feedback_id=new_id("mfb"),
            memory_id=memory_id,
            score=float(body.get("score") or 0),
            comment=str(body.get("comment") or ""),
            actor=str(body.get("actor") or "system"),
        )
        self.feedback.append(fb)
        self._log("feedback", memory_id=memory_id, details={"score": fb.score})
        return fb

    def analytics(self) -> dict[str, Any]:
        by_kind: dict[str, int] = {}
        by_layer: dict[str, int] = {}
        for m in self.memories.values():
            k = m.kind.value if isinstance(m.kind, MemoryKind) else str(m.kind)
            l = m.layer.value if isinstance(m.layer, MemoryLayer) else str(m.layer)
            by_kind[k] = by_kind.get(k, 0) + 1
            by_layer[l] = by_layer.get(l, 0) + 1
        return {
            "memories": len(self.memories),
            "chunks": sum(len(v) for v in self.chunks.values()),
            "embeddings": len(self.embeddings),
            "relations": len(self.relations),
            "sessions": len(self.sessions),
            "history": len(self.history),
            "feedback": len(self.feedback),
            "by_kind": by_kind,
            "by_layer": by_layer,
        }

    def timeline(self, *, limit: int = 100) -> list[dict[str, Any]]:
        events = sorted(self.history, key=lambda h: h.created_at, reverse=True)[:limit]
        return [e.to_dict() for e in events]


project_memory_engine = ProjectMemoryEngine()
