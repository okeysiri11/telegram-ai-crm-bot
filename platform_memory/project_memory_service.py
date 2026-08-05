"""Project Memory Engine service façade — Sprint 36.5."""

from __future__ import annotations

from typing import Any

from platform_memory.project_memory_engine import ProjectMemoryEngine, project_memory_engine
from platform_memory.project_memory_models import MemoryKind, MemoryLayer


class ProjectMemoryService:
    def __init__(self, engine: ProjectMemoryEngine | None = None) -> None:
        self.engine = engine or project_memory_engine

    def reset(self) -> None:
        self.engine.reset()

    def ensure_ready(self) -> None:
        self.engine.ensure_seed()

    def status(self) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "service": "project_memory",
            "canonical": "platform_memory",
            "sprint": "36.5",
            "kinds": [k.value for k in MemoryKind],
            "layers": [l.value for l in MemoryLayer],
            "analytics": self.engine.analytics(),
            "integrations": [
                "ai_runtime",
                "context_engine",
                "workflow",
                "event_bus",
                "service_builder",
            ],
        }

    async def remember(self, body: dict[str, Any]) -> dict[str, Any]:
        self.ensure_ready()
        rec = await self.engine.remember_async(body)
        await self._publish_event("memory.remembered", rec.to_dict())
        return rec.to_dict()

    def get(self, memory_id: str) -> dict[str, Any]:
        self.ensure_ready()
        return self.engine.get(memory_id).to_dict()

    def list_memories(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.ensure_ready()
        return [m.to_dict() for m in self.engine.list_memories(**kwargs)]

    def forget(self, memory_id: str) -> dict[str, Any]:
        ok = self.engine.forget(memory_id)
        return {"forgotten": ok, "memory_id": memory_id}

    async def search(self, body: dict[str, Any]) -> dict[str, Any]:
        self.ensure_ready()
        hits = await self.engine.search(
            str(body.get("query") or ""),
            kind=body.get("kind"),
            layer=body.get("layer"),
            project_id=body.get("project_id"),
            limit=int(body.get("limit") or 10),
            min_score=float(body.get("min_score") or 0.05),
        )
        return {"hits": [h.to_dict() for h in hits], "count": len(hits)}

    def link(self, body: dict[str, Any]) -> dict[str, Any]:
        self.ensure_ready()
        rel = self.engine.link(
            str(body.get("from_id") or body.get("from")),
            str(body.get("to_id") or body.get("to")),
            relation=str(body.get("relation") or "related"),
            weight=float(body.get("weight") or 1.0),
        )
        return rel.to_dict()

    def graph(self, *, project_id: str | None = None) -> dict[str, Any]:
        self.ensure_ready()
        return self.engine.relations_graph(project_id=project_id)

    def create_session(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_ready()
        return self.engine.create_session(body).to_dict()

    def list_sessions(self) -> list[dict[str, Any]]:
        self.ensure_ready()
        return [s.to_dict() for s in self.engine.list_sessions()]

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self.engine.get_session(session_id).to_dict()

    def pin(self, session_id: str, memory_id: str) -> dict[str, Any]:
        return self.engine.pin_to_session(session_id, memory_id).to_dict()

    def timeline(self, *, limit: int = 100) -> list[dict[str, Any]]:
        self.ensure_ready()
        return self.engine.timeline(limit=limit)

    def feedback(self, body: dict[str, Any]) -> dict[str, Any]:
        self.ensure_ready()
        return self.engine.add_feedback(body).to_dict()

    def analytics(self) -> dict[str, Any]:
        self.ensure_ready()
        return self.engine.analytics()

    def chunks(self, memory_id: str) -> list[dict[str, Any]]:
        self.ensure_ready()
        return [c.to_dict() for c in self.engine.chunks.get(memory_id, [])]

    # --- Integrations ---

    async def for_ai_runtime(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        self.ensure_ready()
        query = str(body.get("query") or body.get("prompt") or "")
        hits = await self.engine.search(query or "project", project_id=body.get("project_id"), limit=5)
        if body.get("write"):
            await self.remember(
                {
                    "kind": "agent",
                    "layer": "working",
                    "title": "AI runtime note",
                    "content": str(body.get("write")),
                    "agent_id": body.get("agent_id") or "ai_runtime",
                    "project_id": body.get("project_id"),
                }
            )
        return {
            "consumer": "ai_runtime",
            "hits": [h.to_dict() for h in hits],
            "prompt_context": "\n".join(f"- {h.title}: {h.snippet}" for h in hits),
        }

    async def for_context_engine(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        self.ensure_ready()
        hits = await self.engine.search(
            str(body.get("query") or "context"),
            project_id=body.get("project_id"),
            limit=8,
        )
        return {
            "consumer": "context_engine",
            "fragments": [
                {
                    "source": "project",
                    "key": h.memory_id,
                    "content": h.content,
                    "score": h.score,
                }
                for h in hits
            ],
        }

    async def for_workflow(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        self.ensure_ready()
        hits = await self.engine.search(
            str(body.get("query") or body.get("workflow_id") or "workflow"),
            kind="workflow",
            project_id=body.get("project_id"),
            limit=5,
        )
        if body.get("write"):
            await self.remember(
                {
                    "kind": "workflow",
                    "layer": "short_term",
                    "title": f"Workflow {body.get('workflow_id') or 'run'}",
                    "content": str(body.get("write")),
                    "workflow_id": body.get("workflow_id"),
                    "project_id": body.get("project_id"),
                }
            )
        return {
            "consumer": "workflow",
            "memory": {h.memory_id: h.content for h in hits},
            "hits": [h.to_dict() for h in hits],
        }

    async def for_service_builder(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = await self.for_context_engine(body)
        data["consumer"] = "service_builder"
        return data

    async def _publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        try:
            from platform_enterprise_event_bus.service import enterprise_event_bus_service as eeb

            await eeb.publish(
                {
                    "topic": "memory",
                    "event_type": event_type,
                    "payload": payload,
                    "source_service": "project_memory",
                }
            )
        except Exception:
            try:
                from events.publisher import publish
                from events.base_event import BaseEvent

                class _MemEvent(BaseEvent):
                    event_type = event_type

                await publish(_MemEvent(payload=payload), wait=False)  # type: ignore[call-arg]
            except Exception:
                pass


project_memory_service = ProjectMemoryService()
