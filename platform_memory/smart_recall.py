"""Epic 45.2 — Smart Recall (продолжим / что делали / что осталось)."""

from __future__ import annotations

import re
from typing import Any

from platform_memory.conversation_memory import conversation_memory
from platform_memory.long_term_memory import long_term_memory
from platform_memory.memory_permissions import MemoryPrincipal
from platform_memory.memory_timeline import memory_timeline
from platform_memory.working_memory import working_memory

RECALL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"продолж\w*\s+проект|продолжить\s+проект", re.I), "project"),
    (re.compile(r"продолж\w*\s+генерац", re.I), "generation"),
    (re.compile(r"верн\w*\s+к\s+реклам|реклам", re.I), "ads"),
    (re.compile(r"что\s+мы\s+делали|что\s+делали\s+вчера|истори[яию]|напомни|покажи\s+истори", re.I), "history"),
    (re.compile(r"последн\w*\s+задач|покажи\s+задач", re.I), "tasks"),
    (re.compile(r"что\s+осталось|осталось\s+сделать", re.I), "remaining"),
    (re.compile(r"продолж(им|ай|ить)?|continue", re.I), "continue"),
]


class SmartRecall:
    def detect_intent(self, text: str) -> str | None:
        raw = (text or "").strip()
        if not raw:
            return None
        for pattern, intent in RECALL_PATTERNS:
            if pattern.search(raw):
                return intent
        return None

    def recall(self, principal: MemoryPrincipal, text: str, *, channel: str = "web") -> dict[str, Any]:
        intent = self.detect_intent(text) or "continue"
        unfinished = working_memory.unfinished(principal)
        tasks = working_memory.open_tasks(principal)
        history = conversation_memory.history(principal, limit=10)
        timeline = memory_timeline.view(principal, window="yesterday" if "вчера" in (text or "").lower() else "today")
        prefs = long_term_memory.all_preferences(principal)

        suggestions: list[str] = []
        for item in unfinished[:5]:
            suggestions.append(f"Продолжить: {item.get('title')}")
        if not suggestions:
            suggestions = ["Продолжить работу", "Открыть AI Command", "Посмотреть таймлайн"]

        reply_map = {
            "continue": "Продолжаем с того места, где остановились.",
            "history": "Вот что было недавно:",
            "tasks": "Последние задачи:",
            "project": "Возвращаемся к проекту.",
            "ads": "Возвращаемся к рекламе.",
            "generation": "Продолжаем генерацию.",
            "remaining": "Вот что осталось сделать:",
        }
        return {
            "intent": intent,
            "reply_ru": reply_map.get(intent, reply_map["continue"]),
            "unfinished": unfinished[:10],
            "tasks": tasks[:10],
            "recent_turns": history[-5:],
            "timeline": timeline,
            "preferences": prefs,
            "suggestions": suggestions,
            "channel": channel,
        }


smart_recall = SmartRecall()
