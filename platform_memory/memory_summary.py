"""Epic 45.2 — Conversation summary (decisions, open questions, next actions)."""

from __future__ import annotations

from typing import Any

from platform_memory.continuity_store import continuity_store, new_id
from platform_memory.conversation_memory import conversation_memory
from platform_memory.memory_permissions import MemoryPrincipal


class MemorySummary:
    def summarize_session(
        self,
        principal: MemoryPrincipal,
        *,
        session_id: str | None = None,
        channel: str = "web",
    ) -> dict[str, Any]:
        turns = conversation_memory.history(principal, session_id=session_id, limit=100)
        if not turns:
            summary = {
                "summary_ru": "Разговор пока пуст.",
                "decisions": [],
                "open_questions": [],
                "next_actions": [],
                "turn_count": 0,
            }
        else:
            texts = [t.get("content", "") for t in turns]
            decisions = [t for t in texts if any(k in t.lower() for k in ("решили", "решение", "согласован", "утверд"))]
            questions = [t for t in texts if "?" in t or t.strip().endswith("?")]
            actions = [t for t in texts if any(k in t.lower() for k in ("нужно", "сделать", "продолж", "запуст", "создай"))]
            brief = " ".join(texts[-5:])[:400]
            summary = {
                "summary_ru": f"Краткое резюме ({len(turns)} реплик): {brief}",
                "decisions": decisions[-5:],
                "open_questions": questions[-5:],
                "next_actions": actions[-5:] or ["Продолжить работу"],
                "turn_count": len(turns),
            }
        key = conversation_memory.session_key(principal.owner_id, session_id)
        summary["id"] = new_id("sum")
        summary["session_key"] = key
        summary["channel"] = channel
        continuity_store.summaries[key] = summary
        return summary

    def get(self, principal: MemoryPrincipal, session_id: str | None = None) -> dict[str, Any] | None:
        key = conversation_memory.session_key(principal.owner_id, session_id)
        return continuity_store.summaries.get(key)


memory_summary = MemorySummary()
