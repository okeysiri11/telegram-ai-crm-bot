"""Epic 45.2 — AI Resume after login."""

from __future__ import annotations

from typing import Any

from platform_memory.conversation_memory import conversation_memory
from platform_memory.long_term_memory import long_term_memory
from platform_memory.memory_permissions import MemoryPrincipal
from platform_memory.memory_timeline import memory_timeline
from platform_memory.working_memory import working_memory


class AiResume:
    def build(self, principal: MemoryPrincipal, *, channel: str = "web") -> dict[str, Any]:
        unfinished = working_memory.unfinished(principal)
        tasks = working_memory.open_tasks(principal)
        projects = [
            p
            for p in working_memory.unfinished(principal, limit=50)
            if p.get("kind") == "project"
        ]
        recent = conversation_memory.history(principal, limit=5)
        timeline = memory_timeline.view(principal, window="today", limit=10)
        prefs = long_term_memory.all_preferences(principal)
        recommend = []
        for item in unfinished[:3]:
            recommend.append(
                {
                    "title": item.get("title"),
                    "action": "continue",
                    "id": item.get("id"),
                    "kind": item.get("kind"),
                }
            )
        if not recommend:
            recommend.append({"title": "Начать новый диалог", "action": "new_chat", "id": None, "kind": "chat"})

        welcome = "Добро пожаловать."
        lang = prefs.get("language")
        if lang and lang.lower().startswith("en"):
            welcome = "Welcome back."

        return {
            "welcome_ru": welcome,
            "last_activity": timeline["events"][:1],
            "last_project": projects[0] if projects else None,
            "unfinished_tasks": tasks[:10],
            "last_conversation": recent[-3:],
            "running_agents": [],  # filled by Hercules adapter when available
            "recommend": recommend,
            "suggestions_ru": [f"Рекомендуем продолжить: {r['title']}" for r in recommend if r.get("title")],
            "channel": channel,
            "owner_id": principal.owner_id,
            "company_id": principal.company_id,
        }

    def text_ru(self, principal: MemoryPrincipal) -> str:
        data = self.build(principal)
        lines = [data["welcome_ru"], "", "Последняя активность:"]
        if data["last_activity"]:
            lines.append(f"• {data['last_activity'][0].get('title')}")
        else:
            lines.append("• пока нет событий")
        if data["last_project"]:
            lines.append(f"Последний проект: {data['last_project'].get('title')}")
        lines.append("Незавершённые задачи:")
        for t in data["unfinished_tasks"][:5]:
            lines.append(f"• {t.get('title')}")
        if not data["unfinished_tasks"]:
            lines.append("• нет открытых задач")
        lines.append("")
        for s in data["suggestions_ru"][:3]:
            lines.append(s)
        return "\n".join(lines)


ai_resume = AiResume()
