"""Enterprise Context Engine service façade — Sprint 36.4."""

from __future__ import annotations

from typing import Any

from platform_memory.runtime_engine import ContextEngine, context_engine
from platform_memory.runtime_models import ContextSourceType


class ContextEngineService:
    def __init__(self, engine: ContextEngine | None = None) -> None:
        self.engine = engine or context_engine

    def reset(self) -> None:
        self.engine.reset()

    def ensure_ready(self) -> None:
        self.engine.sources.ensure_seed()
        self.engine.policies.ensure_defaults()

    def status(self) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "service": "context_engine",
            "canonical": "platform_memory",
            "sprint": "36.4",
            "sources": [s.value for s in ContextSourceType],
            "statistics": self.engine.statistics(),
            "integrations": ["ai_runtime", "workflow", "service_builder"],
        }

    async def resolve(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_ready()
        bundle = await self.engine.resolve(body or {})
        return bundle.to_dict()

    def list_sources(self) -> list[dict[str, Any]]:
        self.ensure_ready()
        return self.engine.sources.list_sources()

    def graph(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build context graph from collected/filtered fragments."""
        self.ensure_ready()
        body = body or {}
        fragments = self.engine.sources.collect(sources=body.get("sources"), query=body)
        filtered, _ = self.engine.policies.filter_fragments(
            fragments,
            principal=str(body.get("principal") or "system"),
            isolation_key=body.get("isolation_key"),
        )
        ranked = self.engine.prioritize(filtered, query=str(body.get("query") or ""))
        merged = self.engine.merge(ranked)
        g = self.engine.graph_builder.build(merged, session_id=body.get("session_id"))
        return g.to_dict()

    def create_session(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.engine.create_session(body).to_dict()

    def list_sessions(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.engine.list_sessions()]

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self.engine.get_session(session_id).to_dict()

    def cache_entries(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.engine.cache.list_entries()]

    def cache_stats(self) -> dict[str, Any]:
        return self.engine.cache.stats()

    def clear_cache(self) -> dict[str, Any]:
        self.engine.cache.reset()
        return self.engine.cache.stats()

    def history(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [h.to_dict() for h in self.engine.history[-limit:]]

    def permissions(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self.engine.policies.list_permissions()]

    def grant_permission(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.policies.grant(body).to_dict()

    def statistics(self) -> dict[str, Any]:
        self.ensure_ready()
        return self.engine.statistics()

    def embeddings(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return self.engine.embeddings[-limit:]

    # --- Integrations ---

    async def for_ai_runtime(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Bundle shaped for AI Runtime / AIService injection."""
        payload = {
            "use_cache": True,
            "max_tokens": 1536,
            **(body or {}),
            "sources": (body or {}).get("sources")
            or [
                "user_profile",
                "conversation_history",
                "agent_memory",
                "knowledge_base",
                "runtime_variables",
                "project",
            ],
        }
        bundle = await self.resolve(payload)
        prompt_context = bundle["prompt_context"]
        project_memory = None
        if (body or {}).get("use_project_memory", True):
            try:
                from platform_memory.project_memory_service import project_memory_service

                project_memory = await project_memory_service.for_context_engine(
                    {
                        "query": (body or {}).get("query") or "",
                        "project_id": (body or {}).get("project_id"),
                    }
                )
                extra = "\n".join(
                    f"- {f.get('content')}" for f in (project_memory.get("fragments") or [])[:5]
                )
                if extra:
                    prompt_context = f"{prompt_context}\n\n[project_memory]\n{extra}".strip()
            except Exception:
                pass
        return {
            "consumer": "ai_runtime",
            "prompt_context": prompt_context,
            "total_tokens": bundle["total_tokens"],
            "sources_used": bundle["sources_used"],
            "bundle_id": bundle["bundle_id"],
            "memory": {
                "prompt_context": prompt_context,
                "fragments": bundle["fragments"],
            },
            "project_memory": project_memory,
        }

    async def for_workflow(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Inject into Workflow RuntimeContext.memory / vars."""
        payload = {
            "use_cache": True,
            "max_tokens": 1024,
            **(body or {}),
            "sources": (body or {}).get("sources")
            or [
                "workflow_state",
                "runtime_variables",
                "project",
                "organization",
                "agent_memory",
            ],
        }
        bundle = await self.resolve(payload)
        return {
            "consumer": "workflow",
            "memory": {
                "prompt_context": bundle["prompt_context"],
                "sources_used": bundle["sources_used"],
                "fragments": {f["key"]: f["content"] for f in bundle["fragments"]},
            },
            "vars": {
                "context_bundle_id": bundle["bundle_id"],
                "context_tokens": bundle["total_tokens"],
            },
            "bundle_id": bundle["bundle_id"],
        }

    async def for_service_builder(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Context available to Service Builder sandboxed services."""
        payload = {
            "use_cache": True,
            "max_tokens": 1024,
            **(body or {}),
            "sources": (body or {}).get("sources")
            or [
                "organization",
                "workspace",
                "documents",
                "knowledge_base",
                "runtime_variables",
            ],
        }
        bundle = await self.resolve(payload)
        return {
            "consumer": "service_builder",
            "context": bundle["prompt_context"],
            "sources_used": bundle["sources_used"],
            "bundle_id": bundle["bundle_id"],
            "permissions_required": ["context.read"],
        }


context_engine_service = ContextEngineService()
