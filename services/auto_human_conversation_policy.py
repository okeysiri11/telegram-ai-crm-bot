"""Sprint 46.1 — Human Conversation Policy (wording + conversational behavior)."""

from __future__ import annotations

from typing import Any

# Auto defaults (Owner Settings → AI → Стиль общения)
DEFAULT_AI_STYLE: dict[str, Any] = {
    "conversation_style": "concise",  # concise | standard | detailed
    "ask_optional_questions": False,
    "confirm_understood": "ambiguity_only",  # always | ambiguity_only | never
    "cross_sell": False,
    "max_clarifying_questions": 1,
    "show_technical_classification": False,
    "human_conversation_guard": True,
    "search_immediately": True,
}

STYLE_LABELS_RU = {
    "concise": "Краткий",
    "standard": "Стандартный",
    "detailed": "Подробный",
}

SHORT_CONTEXTUAL_REPLIES = frozenset(
    {
        "да",
        "нет",
        "1",
        "2",
        "не важно",
        "неважно",
        "любой",
        "любая",
        "сюда",
        "этот",
        "эта",
        "без vin",
        "без вин",
        "ищи",
        "давай",
        "ок",
        "хорошо",
        "пропустить",
        "skip",
        "-",
    }
)

VIN_SKIP_TOKENS = frozenset(
    {
        "нет",
        "no",
        "2",
        "пропустить",
        "skip",
        "-",
        "без vin",
        "без вин",
        "не надо",
        "не нужно",
    }
)

VIN_YES_TOKENS = frozenset({"да", "yes", "1", "добавить", "vin", "добавить vin"})


def resolve_ai_style(settings: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(DEFAULT_AI_STYLE)
    if settings:
        for k, v in settings.items():
            if k in out or k in {
                "max_clarifying_questions",
                "search_immediately",
                "debug_mode",
            }:
                out[k] = v
        # alias
        if "max_clarifications" in settings:
            out["max_clarifying_questions"] = settings["max_clarifications"]
    return out


def is_short_contextual(text: str) -> bool:
    low = (text or "").strip().lower()
    return low in SHORT_CONTEXTUAL_REPLIES


def style_menu_text_ru(settings: dict[str, Any]) -> str:
    st = resolve_ai_style(settings)
    return (
        "🗣 Стиль общения (AI)\n\n"
        f"Стиль: {STYLE_LABELS_RU.get(st['conversation_style'], st['conversation_style'])}\n"
        f"Опциональные вопросы: {'вкл' if st['ask_optional_questions'] else 'выкл'}\n"
        f"Подтверждение: только при неоднозначности\n"
        f"Cross-sell: {'вкл' if st['cross_sell'] else 'выкл'}\n"
        f"Макс. уточнений: {st['max_clarifying_questions']}\n"
        f"Тех. классификация клиенту: выкл\n"
        f"Human Conversation Guard: {'вкл' if st['human_conversation_guard'] else 'выкл'}"
    )


def leasing_ack_ru(*, name: str | None, label: str) -> str:
    who = f", {name}" if name else ""
    return f"Принял{who}. Ищу варианты {label} под эти условия."


def leasing_results_intro_ru() -> str:
    return "Нашёл несколько вариантов. Отправляю ниже."


def leasing_closing_ru() -> str:
    return "Посмотрите. Если понадобится — уточню расчёт или подберу ещё."


def vin_skipped_ack_ru() -> str:
    return "Хорошо, без VIN."


def vin_ask_only_ru() -> str:
    return "Введите VIN автомобиля:"
