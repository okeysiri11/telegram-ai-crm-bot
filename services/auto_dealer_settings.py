"""Sprint 46.1 — Dealer configuration + Owner Auto AI controls."""

from __future__ import annotations

import threading
from typing import Any

DEALER_SETTINGS_SECTIONS = (
    ("sources", "Источники поиска"),
    ("rates", "Курсы"),
    ("commissions", "Комиссии"),
    ("tariffs", "Тарифы"),
    ("services", "Услуги"),
    ("contacts", "Контакты"),
    ("cities", "Города"),
    ("brands", "Бренды"),
    ("telegram_channels", "Telegram-каналы"),
    ("partners", "Партнёры"),
    ("warehouse", "Склад"),
    ("ai_rules", "Правила AI"),
)

PLAN_LABELS_RU = {
    "starter": "Старт",
    "pro": "Профессиональный",
    "business": "Бизнес",
    "enterprise": "Корпоративный",
    "STARTER": "Старт",
    "PRO": "Профессиональный",
    "BUSINESS": "Бизнес",
    "ENTERPRISE": "Корпоративный",
}

DEFAULT_OWNER_CONTROLS: dict[str, Any] = {
    "max_clarifying_questions": 1,
    "search_immediately": True,
    "default_city": "Одесса",
    "default_country": "UA",
    "default_currency": "USD",
    "preferred_sources": [],
    "excluded_sources": [],
    "preferred_dealers": [],
    "telegram_channels": [],
    "max_results": 7,
    "ranking_rules": ["price_asc", "year_desc"],
    "debug_mode": False,
    # Owner Settings → AI → Стиль общения
    "conversation_style": "concise",
    "ask_optional_questions": False,
    "confirm_understood": "ambiguity_only",
    "cross_sell": False,
    "show_technical_classification": False,
    "human_conversation_guard": True,
}


class AutoDealerSettingsStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_user: dict[int, dict[str, Any]] = {}

    def get(self, user_id: int) -> dict[str, Any]:
        with self._lock:
            cur = self._by_user.get(user_id)
            if not cur:
                cur = dict(DEFAULT_OWNER_CONTROLS)
                self._by_user[user_id] = cur
            return dict(cur)

    def update(self, user_id: int, **kwargs: Any) -> dict[str, Any]:
        with self._lock:
            cur = self.get(user_id)
            for k, v in kwargs.items():
                if k in DEFAULT_OWNER_CONTROLS or k.startswith("cfg_"):
                    cur[k] = v
            self._by_user[user_id] = cur
            return dict(cur)

    def menu_text_ru(self) -> str:
        lines = ["⚙ Авто → Настройки дилера", ""]
        for _, title in DEALER_SETTINGS_SECTIONS:
            lines.append(f"• {title}")
        lines.append("• Стиль общения (AI)")
        lines.append("")
        lines.append("Правила AI: краткий стиль, без лишних вопросов, Human Guard.")
        return "\n".join(lines)


auto_dealer_settings = AutoDealerSettingsStore()


def plan_label_ru(code: str) -> str:
    return PLAN_LABELS_RU.get(code) or PLAN_LABELS_RU.get(code.lower()) or code
