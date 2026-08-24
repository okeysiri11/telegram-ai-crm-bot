"""AiCommandCenter — main façade (Epic 44.0)."""

from __future__ import annotations

import time
from typing import Any

from platform_ai_command import VERSION
from platform_ai_command.chat.quick_commands import QUICK_COMMANDS, quick_labels
from platform_ai_command.conversation.store import conversation_store
from platform_ai_command.core.models import Attachment, CommandMessage, CommandResult
from platform_ai_command.executor.hercules_executor import execute_plan
from platform_ai_command.history.store import command_history
from platform_ai_command.memory.context import context_memory
from platform_ai_command.permissions.access import filter_tools_for_role
from platform_ai_command.planner.planner import build_plan, plan_titles
from platform_ai_command.router.command_router import route_command
from platform_ai_command.tools.catalog import TOOLS, list_tools
from platform_ai_command.voice.parser import parse_voice_transcript
from platform_ai_command.router.vertical_router import VERTICALS


def _sanitize_web_reply(text: str) -> str:
    """Hide executor jargon from web Concierge clients; meta stays in response fields."""
    out = (text or "").strip()
    out = out.replace("Готово через Hercules.", "✅ Готово.")
    lines = [
        ln
        for ln in out.splitlines()
        if not ln.strip().lower().startswith(("вертикаль:", "цепочка:", "стоимость"))
    ]
    return "\n".join(lines).strip() or out


class AiCommandCenter:
    """Universal AI Operating System entry — routes → plan → Hercules."""

    VERSION = VERSION

    def __init__(self) -> None:
        self._active: dict[str, dict[str, Any]] = {}

    def home(self, owner_id: str) -> dict[str, Any]:
        hist = command_history.list(owner_id, limit=8)
        return {
            "title": "AI Command Center",
            "version": self.VERSION,
            "sections": [
                "Новый диалог",
                "Последние задачи",
                "Активные генерации",
                "История",
                "Избранное",
                "Вертикали",
                "Голосовой режим",
                "Центр агентов",
                "Статистика",
            ],
            "quick_commands": quick_labels(),
            "verticals": list(VERTICALS),
            "tools": [{"id": t.id, "name_ru": t.name_ru} for t in TOOLS],
            "recent": hist,
            "favorites": command_history.favorites(owner_id),
            "active": list(self._active.get(owner_id, {}).values()),
            "stats": self.stats(owner_id),
        }

    def stats(self, owner_id: str) -> dict[str, Any]:
        items = command_history.list(owner_id, limit=100)
        return {
            "tasks": len(items),
            "cost_total": round(sum(float(i.get("cost") or 0) for i in items), 4),
            "favorites": len(command_history.favorites(owner_id)),
        }

    def new_dialog(self, owner_id: str, session_id: str | None = None) -> str:
        key = conversation_store.key(owner_id, session_id)
        conversation_store.new_dialog(key)
        return key

    async def handle(
        self,
        text: str,
        *,
        owner_id: str,
        channel: str = "web",
        session_id: str | None = None,
        role: str = "owner",
        attachments: list[Attachment] | None = None,
        voice: bool = False,
        max_steps: int | None = None,
        active_vertical: str | None = None,
        active_persona: str | None = None,
        authenticated_role: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        raw = parse_voice_transcript(text) if voice or channel == "voice" else text
        # Prefer live vertical session over sticky memory
        if active_vertical:
            context_memory.update(
                owner_id,
                vertical=active_vertical,
                role=active_persona,
                authenticated_role=authenticated_role,
            )
        enriched = context_memory.enrich_prompt(owner_id, raw)
        msg = CommandMessage(
            text=enriched,
            owner_id=owner_id,
            channel=channel,
            session_id=session_id,
            attachments=list(attachments or []),
            role=role,
            tenant_id=tenant_id,
            meta={
                "active_vertical": active_vertical
                or context_memory.get(owner_id).get("vertical"),
                "active_persona": active_persona,
                "authenticated_role": authenticated_role or role,
                "preferred_vertical": active_vertical
                or context_memory.get(owner_id).get("vertical"),
            },
        )
        key = conversation_store.key(owner_id, session_id)
        conversation_store.add(key, "user", raw)

        route = route_command(msg)
        route.tools = filter_tools_for_role(role, route.tools)

        if route.needs_clarify:
            q = route.clarify_question or "Уточните задачу."
            if channel == "web":
                q = _sanitize_web_reply(q)
            conversation_store.add(key, "assistant", q)
            return {
                "status": "clarify",
                "reply_ru": q,
                "route": {
                    "task": route.task_kind.value,
                    "vertical": route.vertical,
                    "needs_clarify": True,
                },
            }

        if route.vertical:
            context_memory.update(owner_id, vertical=route.vertical)

        plan = build_plan(msg, route)
        # For expensive ad chains in tests / interactive, allow limiting steps
        result = await execute_plan(plan, max_steps=max_steps)
        reply = result.reply_ru
        if channel == "web":
            reply = _sanitize_web_reply(reply)
        conversation_store.add(key, "assistant", reply, plan_id=plan.id)
        command_history.add(owner_id, plan, result)
        self._active.setdefault(owner_id, {})[plan.id] = {
            "plan_id": plan.id,
            "status": result.status,
            "titles": plan_titles(plan),
            "ts": time.time(),
        }
        return {
            "status": result.status,
            "reply_ru": reply,
            "plan_id": plan.id,
            "steps": plan_titles(plan),
            "hercules_job_ids": result.hercules_job_ids,
            "cost": result.cost,
            "duration_sec": result.duration_sec,
            "route": {
                "task": route.task_kind.value,
                "vertical": route.vertical,
                "agents": route.agents,
                "tools": route.tools,
                "cost_estimate": route.cost_estimate,
            },
            "retry": True,
        }

    async def retry(self, owner_id: str, plan_id: str) -> dict[str, Any]:
        entry = command_history.get(owner_id, plan_id)
        if not entry:
            return {"status": "ошибка", "reply_ru": "Задача не найдена."}
        return await self.handle(entry["prompt"], owner_id=owner_id, channel="web")

    def telegram_menu_labels(self) -> list[str]:
        # Sprint 46.5 — vertical labels (Auto/Agro/Beauty/Crypto) are navigation,
        # not AI intents. Generative / CRM tools stay here.
        return [
            "💬 Новый чат",
            "🎙 Голосовой режим",
            "🎨 Создать изображение",
            "🎬 Создать видео",
            "🎤 Озвучить",
            "📄 Документ",
            "📊 CRM",
            "⚙ Настройки",
        ]


ai_command_center = AiCommandCenter()
