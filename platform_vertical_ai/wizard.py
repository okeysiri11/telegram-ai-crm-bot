"""Master creation wizard + multimodal chain for a vertical."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_vertical_ai.models import VerticalConfig, WizardQuestion


@dataclass
class WizardDraft:
    vertical_id: str
    answers: dict[str, str] = field(default_factory=dict)
    step_index: int = 0
    menu_action: str | None = None

    def current(self, questions: tuple[WizardQuestion, ...]) -> WizardQuestion | None:
        if self.step_index >= len(questions):
            return None
        return questions[self.step_index]

    def done(self, questions: tuple[WizardQuestion, ...]) -> bool:
        return self.step_index >= len(questions)


def wizard_steps_as_studio(config: VerticalConfig) -> list[dict[str, Any]]:
    """Convert vertical wizard → Telegram studio step format (≤5 questions)."""
    return [
        {"id": q.id, "prompt": q.question, "choices": list(q.choices) if q.choices else None}
        for q in config.wizard
    ]


def build_vertical_prompt(config: VerticalConfig, answers: dict[str, str], *, intent: str = "") -> str:
    parts = [
        f"Вертикаль: {config.name_ru}.",
        f"Задача: {intent or answers.get('goal') or 'контент'}.",
    ]
    labels = {
        "business": "Бизнес",
        "service": "Услуга",
        "goal": "Цель",
        "audience": "Аудитория",
        "platform": "Площадка",
        "what": "Описание",
        "idea": "Идея",
    }
    for k, label in labels.items():
        if answers.get(k):
            parts.append(f"{label}: {answers[k]}.")
    parts.append("Язык: русский. Результат готов к публикации.")
    return " ".join(parts)


def chain_plan(config: VerticalConfig, answers: dict[str, str]) -> list[dict[str, str]]:
    """Human-readable generation chain (idea → publish) for UX."""
    prompt = build_vertical_prompt(config, answers)
    steps: list[dict[str, str]] = []
    mapping = {
        "prompt": ("Промпт", prompt[:400]),
        "image": ("Изображение", f"Визуал: {answers.get('service') or answers.get('goal') or config.name_ru}"),
        "video": ("Видео", f"Ролик для {answers.get('platform', 'Instagram')}"),
        "voice": ("Озвучка", "Голос под стиль бренда"),
        "music": ("Музыка", "Фоновая музыка под настроение"),
        "reels": ("Reels", "Короткий вертикальный ролик"),
        "caption": ("Описание", f"Текст для {answers.get('platform', 'Instagram')}"),
        "hashtags": ("Хэштеги", f"#{config.id} #маркетинг"),
        "publish_ready": ("Публикация", "Готово к публикации / планированию"),
    }
    for key in config.chain_steps:
        title, detail = mapping.get(key, (key, ""))
        steps.append({"id": key, "title": title, "detail": detail})
    return steps


def calendar_plan(config: VerticalConfig, days: int, *, service: str = "") -> list[dict[str, str]]:
    """Generate a simple content calendar outline."""
    themes = list(config.scenarios) or ["Пост", "Акция", "Видео"]
    offers = list(config.marketing_offers) or ["Акция"]
    plan: list[dict[str, str]] = []
    for i in range(1, min(days, 90) + 1):
        theme = themes[(i - 1) % len(themes)]
        offer = offers[(i - 1) % len(offers)]
        kind = "Reels" if i % 3 == 0 else ("Сторис" if i % 2 == 0 else "Пост")
        plan.append(
            {
                "day": str(i),
                "type": kind,
                "theme": theme if not service else service,
                "hook": offer,
            }
        )
    return plan


def marketing_suggestions(config: VerticalConfig) -> list[str]:
    return list(config.marketing_offers)
