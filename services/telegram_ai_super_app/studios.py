"""Studio dialog helpers — Sprint 43.1 / 43.2 Image / Video / Voice / Prompt / Beauty."""

from __future__ import annotations

from typing import Any

from platform_ai.pipeline_models import BEAUTY_STUDIO_PRODUCTS
from services.telegram_ai_super_app.catalog import (
    IMAGE_PLATFORMS,
    IMAGE_QUALITIES,
    IMAGE_SIZES,
    IMAGE_STYLES,
    PROMPT_CATEGORIES,
    VIDEO_DURATIONS,
    VIDEO_FORMATS,
    VIDEO_FPS,
    VIDEO_STYLES,
    VOICE_MODES,
)
from services.telegram_ai_super_app.concierge import vertical_playbook

# Sprint 43.2 — Beauty Creative Studio scenarios (RU + platform brands)
BEAUTY_SCENARIOS: tuple[str, ...] = (
    "Instagram Post",
    "Instagram Story",
    "Reels",
    "TikTok",
    "Видео акции",
    "Прайс",
    "Подарочный сертификат",
    "Баннер",
    "До / После",
    "Акция месяца",
    "Описание услуги",
    "Контент-план",
    "Ответ клиенту",
    "Ответ в Direct",
    "Ответ в Telegram",
    "Маркетинговый календарь",
)


def image_brief_steps() -> list[dict[str, Any]]:
    return [
        {"id": "what", "prompt": "Описание — что нужно создать?", "choices": None},
        {"id": "size", "prompt": "Размер", "choices": list(IMAGE_SIZES)},
        {"id": "style", "prompt": "Стиль", "choices": list(IMAGE_STYLES)},
        {"id": "platform", "prompt": "Платформа", "choices": list(IMAGE_PLATFORMS)},
        {"id": "count", "prompt": "Количество", "choices": ["1", "3", "5"]},
        {"id": "quality", "prompt": "Качество", "choices": list(IMAGE_QUALITIES)},
    ]


def video_brief_steps() -> list[dict[str, Any]]:
    return [
        {"id": "what", "prompt": "Опишите идею ролика", "choices": None},
        {"id": "script", "prompt": "Раскадровка (или «авто»)", "choices": ["авто"]},
        {"id": "style", "prompt": "Стиль", "choices": list(VIDEO_STYLES)},
        {"id": "duration", "prompt": "Продолжительность", "choices": list(VIDEO_DURATIONS)},
        {"id": "fps", "prompt": "Частота кадров", "choices": list(VIDEO_FPS)},
        {"id": "format", "prompt": "Соотношение сторон", "choices": list(VIDEO_FORMATS)},
    ]


def voice_brief_steps() -> list[dict[str, Any]]:
    return [
        {"id": "mode", "prompt": "Режим голоса", "choices": list(VOICE_MODES)},
        {"id": "text", "prompt": "Текст для озвучки", "choices": None},
    ]


def prompt_brief_steps() -> list[dict[str, Any]]:
    return [
        {"id": "category", "prompt": "Категория промпта", "choices": list(PROMPT_CATEGORIES)},
        {"id": "goal", "prompt": "Идея пользователя", "choices": None},
        {"id": "audience", "prompt": "Аудитория", "choices": None},
        {"id": "tone", "prompt": "Тон", "choices": ["Деловой", "Дружелюбный", "Премиум", "Дерзкий"]},
    ]


def beauty_brief_steps() -> list[dict[str, Any]]:
    choices = list(dict.fromkeys([*BEAUTY_SCENARIOS, *BEAUTY_STUDIO_PRODUCTS]))
    return [
        {
            "id": "what",
            "prompt": "💄 Студия красоты\nЧто создать?",
            "choices": choices[:16],
        }
    ]


def build_prompt_from_answers(answers: dict[str, str]) -> str:
    return (
        f"Категория: {answers.get('category', 'Маркетинг')}. "
        f"Цель: {answers.get('goal', '')}. "
        f"Аудитория: {answers.get('audience', '')}. "
        f"Тон: {answers.get('tone', 'Деловой')}. "
        "Сгенерируй идеальный промпт на русском, готовый к генерации."
    )


def compose_generation_prompt(studio: str, answers: dict[str, str]) -> str:
    if studio == "prompt":
        return build_prompt_from_answers(answers)
    if studio in ("image", "design"):
        return (
            f"{answers.get('what', '')}. Размер {answers.get('size', '')}, "
            f"стиль {answers.get('style', '')}, платформа {answers.get('platform', '')}, "
            f"качество {answers.get('quality', '')}, вариантов {answers.get('count', '1')}."
        )
    if studio in ("video", "reels"):
        return (
            f"{answers.get('what', '')}. Раскадровка: {answers.get('script', 'авто')}. "
            f"Стиль {answers.get('style', '')}, {answers.get('duration', '')}, "
            f"{answers.get('fps', '30 FPS')}, формат {answers.get('format', '')}."
        )
    if studio == "voice":
        return f"{answers.get('mode', 'Озвучка текста')}: {answers.get('text', '')}"
    if studio == "voice_clone":
        return f"Клон голоса: {answers.get('text', '')}"
    if studio == "text":
        return (
            f"Написать текст: {answers.get('what') or answers.get('idea') or ''}. "
            f"Тон: {answers.get('tone', 'Деловой')}."
        )
    if studio == "beauty":
        return f"Студия красоты: {answers.get('what', '')}. Салон, русский язык, готовый контент."
    if studio in ("document", "presentation", "ads"):
        return f"{studio}: {answers.get('what') or answers.get('goal') or answers.get('idea') or 'документ'}"
    book = vertical_playbook(studio if studio in ("auto", "crypto", "agro", "legal") else "")
    topic = answers.get("what") or answers.get("goal") or studio
    items = ", ".join(book.get("items", [])[:5])
    return f"{book.get('title', studio)}: {topic}. Фокус: {items}."


def studio_steps(studio_id: str) -> list[dict[str, Any]]:
    if studio_id in ("image", "design"):
        return image_brief_steps()
    if studio_id in ("video", "reels"):
        return video_brief_steps()
    if studio_id == "voice":
        return voice_brief_steps()
    if studio_id == "prompt":
        return prompt_brief_steps()
    if studio_id == "beauty":
        return beauty_brief_steps()
    if studio_id in ("document", "presentation", "ads"):
        return [{"id": "what", "prompt": "Опишите, что создать", "choices": None}]
    if studio_id in ("auto", "crypto", "agro", "legal"):
        book = vertical_playbook(studio_id)
        return [
            {
                "id": "what",
                "prompt": f"{book['title']}\nЧто создать?",
                "choices": list(book["items"])[:8],
            }
        ]
    return [{"id": "what", "prompt": "Опишите задачу", "choices": None}]
