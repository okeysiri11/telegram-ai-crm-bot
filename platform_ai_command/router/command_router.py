"""Command router — task kind, agents, tools, cost, access."""

from __future__ import annotations

import re

from platform_ai_command.core.models import CommandMessage, RouteDecision, TaskKind
from platform_ai_command.router.vertical_router import (
    CLARIFY_MARKETING_RU,
    CLARIFY_RU,
    detect_vertical,
    needs_clarify,
)

_TASK_RULES: list[tuple[re.Pattern[str], TaskKind, list[str], list[str], float]] = [
    (re.compile(r"изображ|картинк|баннер|фото|image", re.I), TaskKind.IMAGE, ["designer"], ["generate_image"], 0.05),
    (re.compile(r"видео|reels|ролик|tiktok|shorts", re.I), TaskKind.VIDEO, ["video"], ["generate_video"], 0.2),
    (re.compile(r"озвуч|голос|voice|tts", re.I), TaskKind.VOICE, ["voice"], ["generate_voice"], 0.04),
    (re.compile(r"презентац", re.I), TaskKind.PRESENTATION, ["copywriter"], ["create_presentation"], 0.06),
    (re.compile(r"документ|договор|pdf|word|excel", re.I), TaskKind.DOCUMENT, ["copywriter"], ["analyze_document", "write_text"], 0.05),
    (re.compile(r"перевод|перевед", re.I), TaskKind.TRANSLATE, ["copywriter"], ["translate"], 0.02),
    (re.compile(r"ocr|распозна", re.I), TaskKind.OCR, ["copywriter"], ["ocr"], 0.03),
    (re.compile(r"найди|поиск|search", re.I), TaskKind.SEARCH, ["analyst"], ["search"], 0.01),
    (re.compile(r"опубликуй|публикац", re.I), TaskKind.PUBLISH, ["marketing"], ["publish"], 0.02),
    (re.compile(r"workflow|автоматизац", re.I), TaskKind.WORKFLOW, ["automation"], ["workflow"], 0.03),
    (re.compile(r"агент|agent", re.I), TaskKind.AGENT, ["orchestrator"], ["write_text"], 0.04),
    (re.compile(r"прибыл|аналит|отч[её]т", re.I), TaskKind.ANALYTICS, ["analyst"], ["erp_action", "write_text"], 0.03),
    (re.compile(r"клиент|сделк|crm", re.I), TaskKind.CRM, ["crm"], ["crm_action"], 0.02),
    (re.compile(r"erp|склад", re.I), TaskKind.ERP, ["erp"], ["erp_action"], 0.02),
    (re.compile(r"реклам", re.I), TaskKind.IMAGE, ["copywriter", "designer", "video", "voice", "marketing"], ["write_text", "generate_image", "generate_video", "generate_voice", "publish"], 0.35),
]


def route_command(message: CommandMessage) -> RouteDecision:
    text = message.text or ""
    task = TaskKind.CHAT
    agents = ["concierge"]
    tools = ["write_text"]
    cost = 0.01
    for pattern, kind, ag, tl, c in _TASK_RULES:
        if pattern.search(text):
            task, agents, tools, cost = kind, ag, tl, c
            break

    # attachments override
    for att in message.attachments:
        if att.kind.value in ("image", "screenshot") and task == TaskKind.CHAT:
            task, tools, cost = TaskKind.IMAGE, ["generate_image", "ocr"], max(cost, 0.05)
        if att.kind.value in ("pdf", "word", "excel", "document"):
            task, tools, cost = TaskKind.DOCUMENT, ["analyze_document"], max(cost, 0.05)
        if att.kind == att.kind.VOICE or att.kind.value == "voice":
            tools = list(dict.fromkeys([*tools, "generate_voice"]))

    vertical, conf = detect_vertical(
        text,
        preferred=(message.meta or {}).get("active_vertical")
        or (message.meta or {}).get("preferred_vertical"),
    )
    marketing_ask = "реклам" in text.lower()
    clarify = needs_clarify(
        text,
        task_implies_vertical=task in (TaskKind.IMAGE, TaskKind.VIDEO) and marketing_ask,
    )
    if clarify and not vertical:
        question = CLARIFY_MARKETING_RU if marketing_ask else CLARIFY_RU
        return RouteDecision(
            task_kind=task,
            vertical=None,
            agents=agents,
            tools=tools,
            providers_hint=["hercules"],
            access_level=message.role,
            cost_estimate=cost,
            needs_clarify=True,
            clarify_question=question,
            confidence=conf,
        )

    access = "owner" if message.role in ("owner", "admin", "platform_owner") else message.role
    return RouteDecision(
        task_kind=task,
        vertical=vertical,
        agents=agents,
        tools=tools,
        providers_hint=["hercules", "unified_pipeline"],
        access_level=access,
        cost_estimate=cost,
        needs_clarify=False,
        confidence=max(conf, 0.55),
    )
