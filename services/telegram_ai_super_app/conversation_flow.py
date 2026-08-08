"""Sprint 43.3 — conversational clarifying flow (short ideas → questions → prompt)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClarifyStep:
    id: str
    question: str
    choices: list[str] | None = None


@dataclass
class ConversationDraft:
    intent: str
    studio_id: str
    answers: dict[str, str] = field(default_factory=dict)
    step_index: int = 0

    def current(self, steps: list[ClarifyStep]) -> ClarifyStep | None:
        if self.step_index >= len(steps):
            return None
        return steps[self.step_index]


# Shared clarifying questions — max ~3 before generate (UX rule).
CLARIFY_BY_INTENT: dict[str, list[ClarifyStep]] = {
    "ads": [
        ClarifyStep("business", "Какой бизнес?", ["Салон красоты", "Автосалон", "Кафе", "Другое"]),
        ClarifyStep("audience", "Какая аудитория?", ["Женщины 25–45", "Мужчины", "Семьи", "Бизнес"]),
        ClarifyStep("goal", "Какая цель?", ["Привлечь клиентов", "Распродажа", "Новый продукт", "Бренд"]),
    ],
    "image": [
        ClarifyStep("what", "Что изобразить?", None),
        ClarifyStep("style", "Какой стиль?", ["Реализм", "Минимализм", "Премиум", "Яркий"]),
        ClarifyStep("platform", "Куда публикуем?", ["Instagram", "Telegram", "Сайт", "Реклама"]),
    ],
    "video": [
        ClarifyStep("what", "О чём видео?", None),
        ClarifyStep("duration", "Длительность?", ["15 сек", "30 сек", "60 сек"]),
        ClarifyStep("format", "Формат?", ["Вертикальное", "Горизонтальное", "Квадрат"]),
    ],
    "reels": [
        ClarifyStep("what", "Тема Reels?", None),
        ClarifyStep("style", "Настроение?", ["Динамично", "Спокойно", "Премиум", "Юмор"]),
    ],
    "voice": [
        ClarifyStep("text", "Какой текст озвучить?", None),
        ClarifyStep("tone", "Какой голос?", ["Диктор", "Дружелюбный", "Рекламный", "Спокойный"]),
    ],
    "voice_clone": [
        ClarifyStep("text", "Текст для озвучки вашим голосом?", None),
    ],
    "document": [
        ClarifyStep("what", "Какой документ нужен?", ["Договор", "КП", "Письмо", "Другое"]),
    ],
    "presentation": [
        ClarifyStep("what", "Тема презентации?", None),
        ClarifyStep("slides", "Сколько слайдов?", ["5", "10", "15"]),
    ],
    "text": [
        ClarifyStep("what", "О чём написать?", None),
        ClarifyStep("tone", "Тон текста?", ["Деловой", "Дружелюбный", "Продающий"]),
    ],
    "prompt": [
        ClarifyStep("goal", "Что должно получиться?", None),
        ClarifyStep("domain", "Сфера?", ["Красота", "Авто", "Юриспруденция", "Маркетинг"]),
    ],
    "beauty": [
        ClarifyStep("what", "Что создать для салона?", None),  # filled from scenarios in UI
    ],
    "generic": [
        ClarifyStep("business", "Какой бизнес?", None),
        ClarifyStep("goal", "Какая цель?", ["Продажи", "Охват", "Доверие", "Заявки"]),
        ClarifyStep("style", "Какой стиль?", ["Премиум", "Простой", "Яркий", "Строгий"]),
    ],
}


def steps_for(studio_id: str) -> list[ClarifyStep]:
    if studio_id in CLARIFY_BY_INTENT:
        return list(CLARIFY_BY_INTENT[studio_id])
    if studio_id in ("design",):
        return list(CLARIFY_BY_INTENT["image"])
    return list(CLARIFY_BY_INTENT["generic"])


def is_short_idea(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 24:
        return True
    words = t.split()
    return len(words) <= 4


def build_prompt_from_draft(draft: ConversationDraft) -> str:
    a = draft.answers
    parts = [f"Задача: {draft.intent}."]
    mapping = {
        "business": "Бизнес",
        "audience": "Аудитория",
        "goal": "Цель",
        "what": "Описание",
        "style": "Стиль",
        "platform": "Платформа",
        "duration": "Длительность",
        "format": "Формат",
        "text": "Текст",
        "tone": "Тон",
        "slides": "Слайды",
        "domain": "Сфера",
    }
    for k, label in mapping.items():
        if a.get(k):
            parts.append(f"{label}: {a[k]}.")
    parts.append("Сделай результат готовым к использованию. Язык — русский.")
    return " ".join(parts)


def preview_brief(draft: ConversationDraft) -> str:
    labels = {
        "business": "Бизнес",
        "audience": "Аудитория",
        "goal": "Цель",
        "what": "Описание",
        "style": "Стиль",
        "platform": "Платформа",
        "duration": "Длительность",
        "format": "Формат",
        "text": "Текст",
        "tone": "Тон",
        "slides": "Слайды",
        "domain": "Сфера",
        "idea": "Идея",
    }
    lines = ["Вот что понял:", ""]
    for k, v in draft.answers.items():
        lines.append(f"• {labels.get(k, k)}: {v}")
    lines.append("")
    lines.append("Могу сгенерировать сейчас.")
    return "\n".join(lines)


def detect_studio_from_text(text: str) -> str:
    q = (text or "").lower()
    if any(x in q for x in ("реклам", "акци")):
        return "ads"
    if "reels" in q or "рилс" in q:
        return "reels"
    if any(x in q for x in ("видео", "ролик")):
        return "video"
    if any(x in q for x in ("озвуч", "голос", "клон")):
        return "voice" if "клон" not in q else "voice_clone"
    if any(x in q for x in ("картин", "изображ", "баннер", "фото")):
        return "image"
    if "презентац" in q:
        return "presentation"
    if any(x in q for x in ("договор", "документ", "кп")):
        return "document"
    if "промпт" in q:
        return "prompt"
    if any(x in q for x in ("салон", "красот", "beauty")):
        return "beauty"
    return "ads" if "хочу" in q else "text"
