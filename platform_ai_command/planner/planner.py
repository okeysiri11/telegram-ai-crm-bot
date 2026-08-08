"""AI Planner — decompose complex commands into Hercules steps."""

from __future__ import annotations

import uuid

from platform_ai_command.core.models import CommandMessage, CommandPlan, PlanStep, RouteDecision, TaskKind
from platform_ai_command.tools.catalog import get_tool


# Classic ad chain for beauty/marketing
AD_CHAIN: tuple[tuple[str, str, str, str], ...] = (
    ("analyze", "Анализ", "write_text", "text"),
    ("copy", "Копирайтер", "write_text", "text"),
    ("design", "Дизайнер", "generate_image", "image"),
    ("gen_image", "Генерация изображения", "generate_image", "image"),
    ("video", "Видео", "generate_video", "video"),
    ("voice", "Озвучка", "generate_voice", "voice"),
    ("subs", "Субтитры", "write_text", "text"),
    ("publish", "Публикация", "publish", "ads"),
    ("report", "Отчёт", "write_text", "text"),
)


def build_plan(message: CommandMessage, route: RouteDecision) -> CommandPlan:
    steps: list[PlanStep] = []
    text_l = (message.text or "").lower()

    if "реклам" in text_l or (route.task_kind == TaskKind.IMAGE and len(route.tools) > 2):
        for sid, title, tool, modality in AD_CHAIN:
            steps.append(
                PlanStep(
                    id=sid,
                    title_ru=title,
                    tool=tool,
                    agent=route.agents[0] if route.agents else None,
                    modality=modality,
                    payload={"prompt": message.text, "vertical": route.vertical},
                )
            )
    else:
        for tool_id in route.tools:
            tool = get_tool(tool_id)
            modality = tool.modality if tool else "text"
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4())[:8],
                    title_ru=tool.name_ru if tool else tool_id,
                    tool=tool_id,
                    agent=route.agents[0] if route.agents else None,
                    modality=modality,
                    payload={"prompt": message.text, "vertical": route.vertical},
                )
            )
        if not steps:
            steps.append(
                PlanStep(
                    id="chat",
                    title_ru="Ответ",
                    tool="write_text",
                    modality="text",
                    payload={"prompt": message.text},
                )
            )

    return CommandPlan.new(message, route, steps)


def plan_titles(plan: CommandPlan) -> list[str]:
    return [s.title_ru for s in plan.steps]
