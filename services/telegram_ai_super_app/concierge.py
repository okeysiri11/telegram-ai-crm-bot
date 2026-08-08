"""AI Concierge — natural language → vertical / agent / workflow / modality."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConciergePlan:
    intent: str
    vertical: str
    agent: str
    workflow: str
    modality: str
    llm_hint: str
    reply_ru: str
    studio_id: str | None = None


_RULES: list[tuple[re.Pattern[str], ConciergePlan]] = [
    (
        re.compile(r"картинк|изображ|фото|баннер|image", re.I),
        ConciergePlan(
            "generate_image",
            "marketing",
            "Image Agent",
            "image_studio",
            "image",
            "vision_llm",
            "Понял. Создаём изображение — уточню пару деталей.",
            "image",
        ),
    ),
    (
        re.compile(r"видео|reels|ролик|клип", re.I),
        ConciergePlan(
            "generate_video",
            "marketing",
            "Video Agent",
            "video_studio",
            "video",
            "video_llm",
            "Понял. Создаём видео.",
            "video",
        ),
    ),
    (
        re.compile(r"голос|озвуч|диктор|tts|voice", re.I),
        ConciergePlan(
            "generate_voice",
            "marketing",
            "Voice Agent",
            "voice_studio",
            "voice",
            "audio_llm",
            "Понял. Подготовлю озвучку.",
            "voice",
        ),
    ),
    (
        re.compile(r"реклам|ads|кампани", re.I),
        ConciergePlan(
            "create_ads",
            "marketing",
            "Marketing AI",
            "ads_pipeline",
            "workflow",
            "chat_llm",
            "Готовлю рекламу. Задам пару уточнений.",
            "ads",
        ),
    ),
    (
        re.compile(r"crm|клиент|сделк|лид", re.I),
        ConciergePlan(
            "crm",
            "crm",
            "CRM AI",
            "crm_assist",
            "text",
            "chat_llm",
            "Контекст CRM. Могу найти клиента, создать сделку или показать задачи.",
            None,
        ),
    ),
    (
        re.compile(r"продаж|аналит|отч[её]т", re.I),
        ConciergePlan(
            "analytics",
            "analytics",
            "Analytics AI",
            "sales_report",
            "text",
            "chat_llm",
            "Соберу аналитику продаж. Уточните период или вертикаль, если нужно.",
            None,
        ),
    ),
    (
        re.compile(r"договор|претензи|иск|юридич|legal", re.I),
        ConciergePlan(
            "legal",
            "legal",
            "Legal AI",
            "legal_docs",
            "text",
            "chat_llm",
            "Юридический AI готов: договор, претензия, письмо или анализ документа.",
            "legal",
        ),
    ),
    (
        re.compile(r"авто|машин|vin|autoria|auto.?ria|olx|объявлен", re.I),
        ConciergePlan(
            "auto_marketing",
            "auto",
            "Auto AI",
            "auto_listings",
            "workflow",
            "chat_llm",
            "Auto AI: объявления, Instagram, TikTok, AutoRia, OLX, Facebook, Shorts.",
            "auto",
        ),
    ),
    (
        re.compile(r"crypto|крипт|otc|амл|aml", re.I),
        ConciergePlan(
            "crypto",
            "crypto",
            "Crypto AI",
            "crypto_content",
            "workflow",
            "chat_llm",
            "Crypto AI: аналитика, реклама, посты, баннеры, OTC-предложения.",
            "crypto",
        ),
    ),
    (
        re.compile(r"агро|agro|зерн|урожа", re.I),
        ConciergePlan(
            "agro",
            "agro",
            "Agro AI",
            "agro_content",
            "workflow",
            "chat_llm",
            "Agro AI: КП, аналитика, цены, презентации и маркетинг.",
            "agro",
        ),
    ),
    (
        re.compile(r"beauty|красот|салон|instagram stories", re.I),
        ConciergePlan(
            "beauty",
            "beauty",
            "Beauty AI",
            "beauty_calendar",
            "workflow",
            "chat_llm",
            "Beauty AI: Instagram, Stories, Reels, TikTok, акции, прайсы, контент-план.",
            "beauty",
        ),
    ),
    (
        re.compile(
            r"лендинг|прибыл|проанализир|проверь продаж|подготовь кп|построй отч|"
            r"покажи прибыл|создай лендинг|создай презентац|сделай реклам",
            re.I,
        ),
        ConciergePlan(
            "owner_ai",
            "owner",
            "Owner AI",
            "owner_assist",
            "text",
            "chat_llm",
            "Owner AI: могу создать лендинг, показать прибыль, проанализировать CRM, "
            "проверить продажи, подготовить КП, построить отчёт, сделать рекламу или презентацию.",
            None,
        ),
    ),
    (
        re.compile(r"опубликуй позже|мультимодаль|цепочк.*реклам|создай рекламу.*изображ", re.I),
        ConciergePlan(
            "multimodal",
            "marketing",
            "AI Консьерж",
            "multimodal_pipeline",
            "workflow",
            "chat_llm",
            "Запускаю мультимодальную цепочку: реклама → изображение → видео → озвучка → публикация.",
            "ads",
        ),
    ),
    (
        re.compile(r"промпт|prompt", re.I),
        ConciergePlan(
            "prompt",
            "ai_studio",
            "Prompt Agent",
            "prompt_studio",
            "prompt",
            "chat_llm",
            "Улучшим промпт — ответьте на пару вопросов.",
            "prompt",
        ),
    ),
    (
        re.compile(r"ai studio|студи|презентац", re.I),
        ConciergePlan(
            "open_studio",
            "ai_studio",
            "AI Консьерж",
            "ai_studio_home",
            "workflow",
            "chat_llm",
            "Открываю Студию AI. Что хотите создать?",
            None,
        ),
    ),
]

_FOLLOW_UP = re.compile(
    r"ещё\s*\d*\s*вариант|измени\s*стиль|сделай\s*лучше|сделай\s*короче|"
    r"перевед|создай\s*видео|создай\s*изображ|создай\s*озвуч",
    re.I,
)


def plan_from_text(text: str, *, last_modality: str | None = None) -> ConciergePlan:
    raw = (text or "").strip()
    if _FOLLOW_UP.search(raw) and last_modality:
        modality = last_modality
        if "видео" in raw.lower():
            modality = "video"
        elif "изображ" in raw.lower() or "картин" in raw.lower():
            modality = "image"
        elif "озвуч" in raw.lower() or "голос" in raw.lower():
            modality = "voice"
        return ConciergePlan(
            "follow_up",
            "ai_studio",
            "AI Консьерж",
            "iterate",
            modality,
            "chat_llm",
            f"Продолжаю без повторного брифа. Учитываю прошлый результат ({last_modality}) → {modality}.",
            modality if modality in ("image", "video", "voice") else None,
        )

    for pattern, plan in _RULES:
        if pattern.search(raw):
            return plan

    return ConciergePlan(
        "general",
        "owner",
        "AI Консьерж",
        "concierge_chat",
        "text",
        "chat_llm",
        "Я AI Консьерж. Напишите, что сделать — или выберите пример ниже. "
        "Если деталей мало, я уточню и предложу сгенерировать.",
        None,
    )


def format_plan_card(plan: ConciergePlan) -> str:
    """User-facing card — no provider / LLM / pipeline jargon."""
    return plan.reply_ru


def vertical_playbook(vertical: str) -> dict[str, Any]:
    books = {
        "beauty": {
            "title": "💄 Студия красоты",
            "items": [
                "Instagram",
                "Stories",
                "Reels",
                "TikTok",
                "Акции",
                "Видео",
                "Фото",
                "Баннеры",
                "Прайсы",
                "Ответы клиентам",
                "Описание услуг",
                "Контент-план",
                "30-дневный маркетинговый календарь",
            ],
        },
        "auto": {
            "title": "🚗 Авто",
            "items": [
                "Подготовка объявлений",
                "Instagram",
                "TikTok",
                "AutoRia",
                "OLX",
                "Facebook",
                "YouTube Shorts",
            ],
        },
        "crypto": {
            "title": "💰 Крипто",
            "items": [
                "Аналитика",
                "Реклама",
                "Посты",
                "Баннеры",
                "Обучающие материалы",
                "OTC-предложения",
            ],
        },
        "agro": {
            "title": "🌾 Агро",
            "items": [
                "Коммерческие предложения",
                "Аналитика",
                "Цены",
                "Презентации",
                "Маркетинг",
            ],
        },
        "legal": {
            "title": "⚖ Юридические услуги",
            "items": [
                "Договоры",
                "Претензии",
                "Письма",
                "Иски",
                "Ответы",
                "Анализ документов",
            ],
        },
    }
    return books.get(
        vertical,
        {"title": "AI", "items": ["Создать контент", "Анализ", "Публикация"]},
    )
