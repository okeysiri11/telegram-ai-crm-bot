"""Epic 45.2 — Context Engine 2.0: assemble context before every AI answer."""

from __future__ import annotations

from typing import Any

from platform_memory.conversation_memory import conversation_memory
from platform_memory.long_term_memory import long_term_memory
from platform_memory.memory_permissions import MemoryPrincipal
from platform_memory.memory_search import memory_search
from platform_memory.memory_timeline import memory_timeline
from platform_memory.working_memory import working_memory


class ContextEngineV2:
    """
    History + active project + documents + recent actions +
    AI Studio / CRM / ERP / Knowledge / Memory → Planner → AI Command → Hercules
    """

    VERSION = "2.0.0"

    def assemble(
        self,
        principal: MemoryPrincipal,
        *,
        prompt: str = "",
        session_id: str | None = None,
        channel: str = "web",
        project_id: str | None = None,
        open_documents: list[str] | None = None,
        extras: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        history = conversation_memory.history(principal, session_id=session_id, limit=20)
        unfinished = working_memory.unfinished(principal, limit=15)
        prefs = long_term_memory.all_preferences(principal)
        timeline = memory_timeline.view(principal, window="today", limit=15)
        knowledge = memory_search.search_knowledge(principal, prompt or "работа", limit=5) if prompt else []

        active_project = None
        if project_id:
            for u in unfinished:
                if u.get("project_id") == project_id or u.get("id") == project_id:
                    active_project = u
                    break
        if active_project is None:
            for u in unfinished:
                if u.get("kind") == "project":
                    active_project = u
                    break

        context = {
            "version": self.VERSION,
            "dialog_history": history,
            "active_project": active_project,
            "open_documents": list(open_documents or []),
            "recent_actions": timeline["events"],
            "ai_studio": [u for u in unfinished if u.get("kind") in ("generation", "image", "video")],
            "crm": [u for u in unfinished if "crm" in (u.get("tags") or []) or u.get("kind") in ("client", "deal")],
            "erp": [u for u in unfinished if "erp" in (u.get("tags") or [])],
            "knowledge": knowledge,
            "memory_preferences": prefs,
            "working": unfinished,
            "channel": channel,
            "prompt": prompt,
            "extras": dict(extras or {}),
        }
        context["prompt_enrichment"] = self.enrich_prompt(prompt, context)
        context["pipeline"] = [
            "context_engine_v2",
            "planner",
            "ai_command_center",
            "hercules",
        ]
        return context

    def enrich_prompt(self, prompt: str, context: dict[str, Any]) -> str:
        bits: list[str] = []
        prefs = context.get("memory_preferences") or {}
        if prefs.get("language"):
            bits.append(f"язык={prefs['language']}")
        if prefs.get("communication_style"):
            bits.append(f"стиль={prefs['communication_style']}")
        ap = context.get("active_project")
        if ap:
            bits.append(f"проект={ap.get('title')}")
        unfinished = context.get("working") or []
        if unfinished:
            bits.append("открыто=" + "; ".join(u.get("title", "") for u in unfinished[:3]))
        hist = context.get("dialog_history") or []
        if hist:
            bits.append(f"реплик_в_сессии={len(hist)}")
        if not bits:
            return prompt
        return f"{prompt}\n\n[context_engine_v2: {'; '.join(bits)}]"


context_engine_v2 = ContextEngineV2()
