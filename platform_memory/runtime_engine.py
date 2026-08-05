"""Enterprise Context Engine — resolve, merge, prioritize, optimize, cache, graph.

Sprint 36.4 — extends platform_memory SoR (wraps ContextAssembler when available).
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from platform_memory.context_policies import ContextPolicyEngine, policy_engine
from platform_memory.context_sources import ContextSourceRegistry, source_registry
from platform_memory.runtime_models import (
    SOURCE_RANK,
    ContextBundle,
    ContextCacheEntry,
    ContextEdge,
    ContextFragment,
    ContextGraph,
    ContextHistoryEntry,
    ContextNode,
    ContextSession,
    ContextSourceType,
    new_id,
)
from platform_memory.summarizer import estimate_tokens, truncate_to_tokens


class ContextCache:
    def __init__(self, *, max_entries: int = 256, ttl_sec: float = 300.0) -> None:
        self._store: dict[str, ContextCacheEntry] = {}
        self._max = max_entries
        self._ttl = ttl_sec
        self.hits = 0
        self.misses = 0

    def reset(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0

    def make_key(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: str) -> ContextCacheEntry | None:
        entry = self._store.get(key)
        if entry is None:
            self.misses += 1
            return None
        if entry.expires_at is not None and entry.expires_at < time.time():
            self._store.pop(key, None)
            self.misses += 1
            return None
        entry.hits += 1
        self.hits += 1
        return entry

    def set(self, key: str, bundle: dict[str, Any], *, ttl_sec: float | None = None) -> ContextCacheEntry:
        ttl = self._ttl if ttl_sec is None else ttl_sec
        entry = ContextCacheEntry(
            cache_key=key,
            bundle=bundle,
            expires_at=time.time() + ttl if ttl else None,
        )
        self._store[key] = entry
        if len(self._store) > self._max:
            oldest = sorted(self._store.values(), key=lambda e: e.created_at)[: len(self._store) - self._max]
            for o in oldest:
                self._store.pop(o.cache_key, None)
        return entry

    def list_entries(self) -> list[ContextCacheEntry]:
        return list(self._store.values())

    def stats(self) -> dict[str, Any]:
        return {"hits": self.hits, "misses": self.misses, "size": len(self._store), "ttl_sec": self._ttl}


class TokenOptimizer:
    def optimize(
        self,
        fragments: list[ContextFragment],
        *,
        max_tokens: int = 2048,
    ) -> tuple[list[ContextFragment], str, int, bool]:
        selected: list[ContextFragment] = []
        total = 0
        truncated = False
        for frag in sorted(fragments, key=lambda f: (f.score, f.priority), reverse=True):
            if total + frag.tokens > max_tokens:
                remaining = max_tokens - total
                if remaining <= 0:
                    truncated = True
                    break
                content = truncate_to_tokens(frag.content, remaining)
                frag = ContextFragment(
                    fragment_id=frag.fragment_id,
                    source=frag.source,
                    key=frag.key,
                    content=content,
                    priority=frag.priority,
                    tokens=estimate_tokens(content),
                    sensitivity=frag.sensitivity,
                    visibility=frag.visibility,
                    expires_at=frag.expires_at,
                    version=frag.version,
                    metadata=frag.metadata,
                    score=frag.score,
                )
                truncated = True
            selected.append(frag)
            total += frag.tokens
            if total >= max_tokens:
                truncated = True
                break
        prompt = "\n\n".join(
            f"[{f.source.value if hasattr(f.source, 'value') else f.source}:{f.key}] {f.content}" for f in selected
        )
        return selected, prompt, estimate_tokens(prompt) if prompt else total, truncated


class ContextGraphBuilder:
    def build(self, fragments: list[ContextFragment], *, session_id: str | None = None) -> ContextGraph:
        nodes: list[ContextNode] = []
        edges: list[ContextEdge] = []
        root_id = new_id("cnode")
        nodes.append(
            ContextNode(
                node_id=root_id,
                label="context_root",
                source="session",
                metadata={"session_id": session_id},
            )
        )
        by_source: dict[str, str] = {}
        for frag in fragments:
            src = frag.source.value if hasattr(frag.source, "value") else str(frag.source)
            if src not in by_source:
                sid = new_id("cnode")
                by_source[src] = sid
                nodes.append(ContextNode(node_id=sid, label=src, source=src))
                edges.append(
                    ContextEdge(
                        edge_id=new_id("cedge"),
                        from_id=root_id,
                        to_id=sid,
                        relation="contains",
                        weight=SOURCE_RANK.get(src, 1) / 100.0,
                    )
                )
            fid = new_id("cnode")
            nodes.append(
                ContextNode(
                    node_id=fid,
                    label=frag.key,
                    source=src,
                    fragment_id=frag.fragment_id,
                )
            )
            edges.append(
                ContextEdge(
                    edge_id=new_id("cedge"),
                    from_id=by_source[src],
                    to_id=fid,
                    relation="fragment",
                    weight=frag.score or 0.5,
                )
            )
        return ContextGraph(nodes=nodes, edges=edges)


class ContextEngine:
    def __init__(
        self,
        *,
        sources: ContextSourceRegistry | None = None,
        policies: ContextPolicyEngine | None = None,
    ) -> None:
        self.sources = sources or source_registry
        self.policies = policies or policy_engine
        self.cache = ContextCache()
        self.optimizer = TokenOptimizer()
        self.graph_builder = ContextGraphBuilder()
        self.sessions: dict[str, ContextSession] = {}
        self.history: list[ContextHistoryEntry] = []
        self._resolve_count = 0
        self.embeddings: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.sources.reset()
        self.policies.reset()
        self.cache.reset()
        self.sessions.clear()
        self.history.clear()
        self.embeddings.clear()
        self._resolve_count = 0

    def _history(self, action: str, *, session_id: str | None = None, details: dict[str, Any] | None = None) -> None:
        self.history.append(
            ContextHistoryEntry(
                history_id=new_id("chist"),
                session_id=session_id,
                action=action,
                details=details or {},
            )
        )
        self.history = self.history[-5000:]

    def create_session(self, body: dict[str, Any] | None = None) -> ContextSession:
        body = body or {}
        session = ContextSession(
            session_id=new_id("csess"),
            user_id=body.get("user_id"),
            tenant_id=body.get("tenant_id"),
            workspace_id=body.get("workspace_id"),
            principal=str(body.get("principal") or body.get("user_id") or "system"),
            expires_at=body.get("expires_at") or (time.time() + 86400),
            metadata=dict(body.get("metadata") or {}),
        )
        self.sessions[session.session_id] = session
        self._history("session_created", session_id=session.session_id)
        return session

    def get_session(self, session_id: str) -> ContextSession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"context session not found: {session_id}")
        return session

    def list_sessions(self) -> list[ContextSession]:
        return sorted(self.sessions.values(), key=lambda s: s.created_at, reverse=True)

    def prioritize(self, fragments: list[ContextFragment], *, query: str = "") -> list[ContextFragment]:
        q = query.lower().strip()
        ranked: list[ContextFragment] = []
        for frag in fragments:
            score = float(frag.priority)
            if q and q in frag.content.lower():
                score += 25.0
            if q and q in frag.key.lower():
                score += 10.0
            frag.score = score
            ranked.append(frag)
        return sorted(ranked, key=lambda f: f.score, reverse=True)

    def merge(self, fragments: list[ContextFragment]) -> list[ContextFragment]:
        """Dedupe by source+key keeping highest score / version."""
        best: dict[str, ContextFragment] = {}
        for frag in fragments:
            src = frag.source.value if hasattr(frag.source, "value") else str(frag.source)
            key = f"{src}:{frag.key}"
            existing = best.get(key)
            if existing is None or frag.score > existing.score or frag.version > existing.version:
                best[key] = frag
        return list(best.values())

    async def resolve(self, body: dict[str, Any] | None = None) -> ContextBundle:
        body = body or {}
        self.sources.ensure_seed()
        self.policies.ensure_defaults()
        self._resolve_count += 1

        session_id = body.get("session_id")
        if body.get("create_session") and not session_id:
            session = self.create_session(body)
            session_id = session.session_id
        session = self.sessions.get(session_id) if session_id else None
        principal = str(body.get("principal") or (session.principal if session else "system"))
        query_text = str(body.get("query") or body.get("message") or "")
        max_tokens = int(body.get("max_tokens") or 2048)
        sources = body.get("sources")
        use_cache = bool(body.get("use_cache", True))

        cache_payload = {
            "sources": sources,
            "query": query_text,
            "principal": principal,
            "max_tokens": max_tokens,
            "isolation_key": body.get("isolation_key"),
            "max_sensitivity": body.get("max_sensitivity"),
            "inject": body.get("inject"),
        }
        cache_key = self.cache.make_key(cache_payload)
        if use_cache:
            hit = self.cache.get(cache_key)
            if hit is not None:
                data = dict(hit.bundle)
                data["cached"] = True
                self._history("cache_hit", session_id=session_id, details={"cache_key": cache_key})
                return self._bundle_from_dict(data)

        collected = self.sources.collect(sources=sources, query=body)
        # optional enrichment from platform memory assembler
        if body.get("use_memory_assembler"):
            collected = await self._enrich_from_memory(collected, body)

        filtered, filtered_count = self.policies.filter_fragments(
            collected,
            principal=principal,
            isolation_key=body.get("isolation_key"),
            max_sensitivity=body.get("max_sensitivity"),
        )
        prioritized = self.prioritize(filtered, query=query_text)
        merged = self.merge(prioritized)
        selected, prompt, total_tokens, truncated = self.optimizer.optimize(merged, max_tokens=max_tokens)
        graph = self.graph_builder.build(selected, session_id=session_id)

        # lightweight embedding stubs for selected fragments
        for frag in selected:
            self.embeddings.append(
                {
                    "embedding_id": new_id("cemb"),
                    "fragment_id": frag.fragment_id,
                    "dims": 8,
                    "vector": [((i + len(frag.content)) % 7) / 7.0 for i in range(8)],
                }
            )
        self.embeddings = self.embeddings[-2000:]

        sources_used = sorted(
            {
                f.source.value if hasattr(f.source, "value") else str(f.source)
                for f in selected
            }
        )
        bundle = ContextBundle(
            bundle_id=new_id("cbun"),
            session_id=session_id,
            fragments=selected,
            prompt_context=prompt,
            total_tokens=total_tokens,
            truncated=truncated,
            cached=False,
            graph=graph,
            sources_used=sources_used,
            filtered_count=filtered_count,
            metadata={"principal": principal, "query": query_text},
        )
        if session:
            session.fragment_ids = [f.fragment_id for f in selected]
            session.updated_at = time.time()

        if use_cache:
            self.cache.set(cache_key, bundle.to_dict())

        self._history(
            "context_resolved",
            session_id=session_id,
            details={
                "fragments": len(selected),
                "tokens": total_tokens,
                "filtered": filtered_count,
                "sources": sources_used,
            },
        )
        return bundle

    async def _enrich_from_memory(
        self,
        fragments: list[ContextFragment],
        body: dict[str, Any],
    ) -> list[ContextFragment]:
        try:
            from platform_memory.memory_service import memory_service
            from platform_memory.models import ContextAssemblyRequest

            memory_service.initialize()
            result = await memory_service.assemble_context(
                ContextAssemblyRequest(
                    session_id=body.get("session_id"),
                    user_id=body.get("user_id"),
                    agent_id=body.get("agent_id"),
                    organization_id=body.get("tenant_id") or body.get("organization_id"),
                    project_id=body.get("project_id"),
                    current_message=body.get("query") or body.get("message"),
                    query=body.get("query"),
                )
            )
            if result.prompt_context:
                fragments.append(
                    ContextFragment(
                        fragment_id=new_id("cfr"),
                        source=ContextSourceType.AGENT_MEMORY,
                        key="assembled_memory",
                        content=result.prompt_context[:4000],
                        priority=85,
                    )
                )
        except Exception:
            pass
        return fragments

    def _bundle_from_dict(self, data: dict[str, Any]) -> ContextBundle:
        fragments = [
            ContextFragment(
                fragment_id=f["fragment_id"],
                source=f["source"],
                key=f["key"],
                content=f["content"],
                priority=int(f.get("priority") or 0),
                tokens=int(f.get("tokens") or 0),
                sensitivity=f.get("sensitivity") or "internal",
                visibility=f.get("visibility") or "tenant",
                expires_at=f.get("expires_at"),
                version=int(f.get("version") or 1),
                metadata=dict(f.get("metadata") or {}),
                score=float(f.get("score") or 0),
            )
            for f in data.get("fragments") or []
        ]
        graph_data = data.get("graph") or {}
        graph = ContextGraph(
            nodes=[ContextNode(**n) for n in graph_data.get("nodes") or []],
            edges=[ContextEdge(**e) for e in graph_data.get("edges") or []],
        )
        return ContextBundle(
            bundle_id=str(data.get("bundle_id") or new_id("cbun")),
            session_id=data.get("session_id"),
            fragments=fragments,
            prompt_context=str(data.get("prompt_context") or ""),
            total_tokens=int(data.get("total_tokens") or 0),
            truncated=bool(data.get("truncated")),
            cached=bool(data.get("cached")),
            graph=graph,
            sources_used=list(data.get("sources_used") or []),
            filtered_count=int(data.get("filtered_count") or 0),
            metadata=dict(data.get("metadata") or {}),
        )

    def statistics(self) -> dict[str, Any]:
        return {
            "resolves": self._resolve_count,
            "sessions": len(self.sessions),
            "history": len(self.history),
            "embeddings": len(self.embeddings),
            "sources": len(self.sources.list_sources()),
            "permissions": len(self.policies.list_permissions()),
            "policy_version": self.policies.version,
            "cache": self.cache.stats(),
        }


context_engine = ContextEngine()
