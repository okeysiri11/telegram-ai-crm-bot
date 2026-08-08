"""Epic 45.2 — Continuous Memory Manager (façade).

All AI actions that need memory go through this manager, then
Context Engine 2.0 → AI Command Center → Hercules.
"""

from __future__ import annotations

from typing import Any

from platform_memory.ai_resume import ai_resume
from platform_memory.context_engine_v2 import context_engine_v2
from platform_memory.continuity_store import MemoryRecord, continuity_store, new_id
from platform_memory.conversation_memory import conversation_memory
from platform_memory.long_term_memory import long_term_memory
from platform_memory.memory_cards import memory_cards
from platform_memory.memory_cleanup import memory_cleanup
from platform_memory.memory_embeddings import memory_embeddings
from platform_memory.memory_permissions import MemoryPrincipal, can_delete, can_write
from platform_memory.memory_search import memory_search
from platform_memory.memory_summary import memory_summary
from platform_memory.memory_timeline import memory_timeline
from platform_memory.smart_recall import smart_recall
from platform_memory.working_memory import working_memory

VERSION = "45.2.0"

SUGGESTION_TEMPLATES = (
    "Продолжить рекламу",
    "Закончить документ",
    "Опубликовать пост",
    "Создать видео",
    "Ответить клиенту",
    "Закрыть задачу",
    "Запустить Workflow",
)


class MemoryManager:
    VERSION = VERSION

    def principal(
        self,
        owner_id: str,
        *,
        company_id: str = "default",
        role: str = "owner",
        project_ids: list[str] | None = None,
    ) -> MemoryPrincipal:
        return MemoryPrincipal(
            owner_id=owner_id,
            company_id=company_id,
            role=role,
            project_ids=tuple(project_ids or ()),
        )

    def status(self, owner_id: str, **kwargs: Any) -> dict[str, Any]:
        p = self.principal(owner_id, **kwargs)
        return {
            "version": self.VERSION,
            "owner_id": owner_id,
            "company_id": p.company_id,
            "levels": ["session", "working", "project", "long_term", "knowledge"],
            "counts": {
                "session": len(continuity_store.list_for(owner_id, level="session", limit=1000)),
                "working": len(continuity_store.list_for(owner_id, level="working", limit=1000)),
                "project": len(continuity_store.list_for(owner_id, level="project", limit=1000)),
                "long_term": len(continuity_store.list_for(owner_id, level="long_term", limit=1000)),
                "knowledge": len(continuity_store.list_for(owner_id, level="knowledge", limit=1000)),
            },
            "cross_platform": True,
            "channels": ["telegram", "web", "desktop", "voice"],
        }

    def save(
        self,
        owner_id: str,
        *,
        title: str,
        content: str,
        level: str = "working",
        kind: str = "note",
        channel: str = "web",
        project_id: str | None = None,
        company_id: str = "default",
        role: str = "owner",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        p = self.principal(owner_id, company_id=company_id, role=role)
        if not can_write(p):
            return {"error": "forbidden"}
        emb = memory_embeddings.embed(f"{title} {content}")
        rec = MemoryRecord(
            id=new_id("mem"),
            owner_id=owner_id,
            company_id=company_id,
            level=level,
            kind=kind,
            title=title,
            content=content,
            channel=channel,
            project_id=project_id,
            role=role,
            tags=list(tags or []),
            embedding=emb,
            metadata=dict(metadata or {}),
        )
        continuity_store.save(rec)
        memory_timeline.record(
            p, action="memory_saved", title=title, channel=channel, project_id=project_id, ref_id=rec.id
        )
        return rec.to_dict()

    def pin(self, owner_id: str, memory_id: str, *, company_id: str = "default") -> dict[str, Any] | None:
        rec = continuity_store.get(memory_id)
        if not rec or rec.owner_id != owner_id:
            return None
        rec.pinned = True
        continuity_store.save(rec)
        return rec.to_dict()

    def remove(self, owner_id: str, memory_id: str, *, company_id: str = "default", role: str = "owner") -> bool:
        p = self.principal(owner_id, company_id=company_id, role=role)
        rec = continuity_store.get(memory_id)
        if not rec or not can_delete(p, rec):
            return False
        return continuity_store.remove(memory_id)

    def search(self, owner_id: str, query: str, **kwargs: Any) -> dict[str, Any]:
        p = self.principal(owner_id, **{k: kwargs[k] for k in ("company_id", "role") if k in kwargs})
        return memory_search.search(p, query, scopes=kwargs.get("scopes"), limit=int(kwargs.get("limit") or 30))

    def context(self, owner_id: str, prompt: str = "", **kwargs: Any) -> dict[str, Any]:
        p = self.principal(
            owner_id,
            company_id=kwargs.get("company_id", "default"),
            role=kwargs.get("role", "owner"),
        )
        return context_engine_v2.assemble(
            p,
            prompt=prompt,
            session_id=kwargs.get("session_id"),
            channel=kwargs.get("channel", "web"),
            project_id=kwargs.get("project_id"),
            open_documents=kwargs.get("open_documents"),
        )

    def timeline(self, owner_id: str, window: str = "today", **kwargs: Any) -> dict[str, Any]:
        p = self.principal(owner_id, company_id=kwargs.get("company_id", "default"))
        return memory_timeline.view(p, window=window, limit=int(kwargs.get("limit") or 100))

    def resume(self, owner_id: str, **kwargs: Any) -> dict[str, Any]:
        p = self.principal(owner_id, company_id=kwargs.get("company_id", "default"))
        return ai_resume.build(p, channel=kwargs.get("channel", "web"))

    def summary(self, owner_id: str, **kwargs: Any) -> dict[str, Any]:
        p = self.principal(owner_id, company_id=kwargs.get("company_id", "default"))
        return memory_summary.summarize_session(
            p, session_id=kwargs.get("session_id"), channel=kwargs.get("channel", "web")
        )

    def project(self, owner_id: str, project_id: str, title: str, **kwargs: Any) -> dict[str, Any]:
        p = self.principal(owner_id, company_id=kwargs.get("company_id", "default"))
        return working_memory.upsert_project(
            p,
            project_id=project_id,
            title=title,
            content=kwargs.get("content", ""),
            channel=kwargs.get("channel", "web"),
            status=kwargs.get("status", "active"),
        )

    def recall(self, owner_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        p = self.principal(owner_id, company_id=kwargs.get("company_id", "default"))
        return smart_recall.recall(p, text, channel=kwargs.get("channel", "web"))

    def suggestions(self, owner_id: str, **kwargs: Any) -> list[dict[str, str]]:
        p = self.principal(owner_id, company_id=kwargs.get("company_id", "default"))
        unfinished = working_memory.unfinished(p, limit=10)
        out: list[dict[str, str]] = []
        for item in unfinished:
            kind = item.get("kind")
            title = item.get("title") or ""
            if kind == "generation" or "реклам" in title.lower():
                out.append({"label": "Продолжить рекламу", "ref_id": item["id"]})
            elif kind == "document":
                out.append({"label": "Закончить документ", "ref_id": item["id"]})
            elif kind == "task":
                out.append({"label": "Закрыть задачу", "ref_id": item["id"]})
            elif kind == "client":
                out.append({"label": "Ответить клиенту", "ref_id": item["id"]})
        for tmpl in SUGGESTION_TEMPLATES:
            if not any(s["label"] == tmpl for s in out):
                out.append({"label": tmpl, "ref_id": ""})
            if len(out) >= 7:
                break
        return out[:7]

    def workspace(self, owner_id: str, **kwargs: Any) -> dict[str, Any]:
        p = self.principal(owner_id, company_id=kwargs.get("company_id", "default"))
        all_items = continuity_store.list_for(owner_id, company_id=p.company_id, limit=200)
        def by_kind(*kinds: str) -> list[dict[str, Any]]:
            return [r.to_dict() for r in all_items if r.kind in kinds][:12]

        return {
            "title": "Моя рабочая область",
            "projects": by_kind("project"),
            "documents": by_kind("document"),
            "images": by_kind("image"),
            "videos": by_kind("video"),
            "generations": by_kind("generation"),
            "prompts": by_kind("prompt"),
            "favorites": [r.to_dict() for r in all_items if r.favorite][:12],
            "drafts": [r.to_dict() for r in all_items if r.draft][:12],
            "continue": working_memory.unfinished(p, limit=10),
            "suggestions": self.suggestions(owner_id, company_id=p.company_id),
            "resume": ai_resume.build(p),
        }

    def telegram_menu(self, owner_id: str) -> dict[str, Any]:
        resume = self.resume(owner_id, channel="telegram")
        return {
            "title": "🧠 Память",
            "welcome": resume.get("welcome_ru"),
            "buttons": [
                "Последние разговоры",
                "Продолжить работу",
                "Проекты",
                "Избранное",
                "Недавние документы",
                "Последние генерации",
                "AI Summary",
                "Поиск",
            ],
        }

    async def run_with_memory(
        self,
        owner_id: str,
        text: str,
        *,
        channel: str = "web",
        company_id: str = "default",
        max_steps: int | None = 3,
    ) -> dict[str, Any]:
        """Smart Recall OR Context Engine 2.0 → ModeManager → AI Command → Hercules."""
        p = self.principal(owner_id, company_id=company_id)
        intent = smart_recall.detect_intent(text)
        if intent:
            recall = smart_recall.recall(p, text, channel=channel)
            conversation_memory.append(p, role="user", content=text, channel=channel)
            conversation_memory.append(
                p, role="assistant", content=recall["reply_ru"], channel=channel
            )
            return {"type": "smart_recall", **recall}

        conversation_memory.append(p, role="user", content=text, channel=channel)
        ctx = context_engine_v2.assemble(p, prompt=text, channel=channel)
        enriched = ctx["prompt_enrichment"]

        # Prefer Dual Experience gate when available
        try:
            from platform_modes.manager import mode_manager

            result = await mode_manager.run_command_if_allowed(
                owner_id, enriched, channel=channel, max_steps=max_steps
            )
        except Exception:
            from platform_ai_command.core.command_center import ai_command_center

            result = await ai_command_center.handle(
                enriched, owner_id=owner_id, channel=channel, max_steps=max_steps
            )
        reply = result.get("reply_ru") or result.get("indicator") or "Готово."
        conversation_memory.append(p, role="assistant", content=str(reply), channel=channel)
        memory_timeline.record(p, action="ai_reply", title=text[:80], channel=channel)
        return {"type": "ai_with_context", "context": ctx, **{k: v for k, v in result.items() if k != "type"}}


memory_manager = MemoryManager()
