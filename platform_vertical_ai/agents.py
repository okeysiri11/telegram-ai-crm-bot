"""Vertical AI agents — copywriter / designer / video / voice / marketing."""

from __future__ import annotations

from typing import Any

from platform_vertical_ai.models import VerticalAgent, VerticalConfig


COPYWRITER_CHANNELS = (
    "Instagram",
    "Telegram",
    "TikTok",
    "Facebook",
    "Google Business",
    "Описание услуги",
    "Ответ клиенту",
    "SEO",
)

DESIGNER_PRODUCTS = (
    "Баннер",
    "Постер",
    "Story",
    "Reels Cover",
    "Меню услуг",
    "Прайс",
    "Сертификат",
    "Визитка",
)

VIDEO_PRODUCTS = (
    "Reels",
    "TikTok",
    "Shorts",
    "Реклама",
    "Видео процедуры",
    "Видео акции",
)

VOICE_PRODUCTS = (
    "Озвучка",
    "Женский голос",
    "Мужской голос",
    "Премиум диктора",
    "Клонирование голоса",
)


def agent_catalog(config: VerticalConfig) -> dict[str, list[str]]:
    """Products each agent can create for this vertical."""
    out: dict[str, list[str]] = {}
    for a in config.agents:
        if a.role == "copywriter":
            out[a.id] = list(COPYWRITER_CHANNELS)
        elif a.role == "designer":
            out[a.id] = list(DESIGNER_PRODUCTS)
        elif a.role == "video":
            out[a.id] = list(VIDEO_PRODUCTS)
        elif a.role == "voice":
            out[a.id] = list(VOICE_PRODUCTS)
        elif a.role == "marketing":
            out[a.id] = list(config.marketing_offers) or ["Акция"]
        else:
            out[a.id] = list(a.capabilities)
    return out


def resolve_agent_task(
    config: VerticalConfig,
    agent_id: str,
    product: str,
    answers: dict[str, str],
) -> dict[str, Any]:
    agent = config.agent(agent_id)
    if not agent:
        agent = VerticalAgent(agent_id, agent_id, "copywriter")
    modality = agent.default_modality
    prompt = (
        f"{config.name_ru} · {agent.name_ru}: {product}. "
        f"Бизнес: {answers.get('business', '')}. "
        f"Услуга: {answers.get('service', answers.get('what', ''))}. "
        f"Цель: {answers.get('goal', '')}. "
        f"Аудитория: {answers.get('audience', '')}. "
        f"Площадка: {answers.get('platform', '')}. "
        "Русский язык, готовый результат."
    )
    return {
        "agent_id": agent.id,
        "agent_name": agent.name_ru,
        "role": agent.role,
        "product": product,
        "modality": modality,
        "prompt": prompt,
        "vertical_id": config.id,
    }
