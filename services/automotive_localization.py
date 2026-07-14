# Automotive module RU/UA localization.

from __future__ import annotations

from typing import Any

DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = frozenset({"ru", "uk"})

VERTICAL_DEEP_LINKS = frozenset({
    "auto",
    "agro",
    "legal",
    "drones",
    "finance",
    "crypto",
    "cafe",
    "beauty",
})

AUTO_ROLE_CODES = (
    "buyer",
    "seller",
    "dealer",
    "marketplace",
    "partner",
    "insurance",
    "bank",
    "logistics",
    "legal_partner",
    "service_station",
    "parts_store",
)

_TEXTS: dict[str, dict[str, str]] = {
    "lang_picker_title": {
        "ru": "🌍 Выберите язык / Оберіть мову",
        "uk": "🌍 Выберите язык / Оберіть мову",
    },
    "lang_russian": {"ru": "🇺🇦 Русский", "uk": "🇺🇦 Русский"},
    "lang_ukrainian": {"ru": "🇺🇦 Українська", "uk": "🇺🇦 Українська"},
    "role_picker_title": {
        "ru": "Выберите вашу роль в автомобильном модуле:",
        "uk": "Оберіть вашу роль в автомобільному модулі:",
    },
    "settings_title": {"ru": "⚙ Настройки", "uk": "⚙ Налаштування"},
    "settings_language": {"ru": "🌍 Язык / Мова", "uk": "🌍 Язык / Мова"},
    "language_saved": {
        "ru": "✅ Язык интерфейса: русский",
        "uk": "✅ Мова інтерфейсу: українська",
    },
    "onboarding_complete": {
        "ru": "✅ Настройка завершена. Добро пожаловать!",
        "uk": "✅ Налаштування завершено. Ласкаво просимо!",
    },
    "tenant_scoped_hint": {
        "ru": "🔒 Вы вошли через tenant-ссылку. Доступен только ваш раздел.",
        "uk": "🔒 Ви увійшли через tenant-посилання. Доступний лише ваш розділ.",
    },
    "auto_hub_title": {
        "ru": "🚗 Авто\n\nАвтомобили, страхование, кредит, лизинг, логистика и юридическая поддержка.\n\nВыберите раздел:",
        "uk": "🚗 Авто\n\nАвтомобілі, страхування, кредит, лізинг, логістика та юридична підтримка.\n\nОберіть розділ:",
    },
    "auto_cars_title": {
        "ru": "🚘 Автомобили\n\nИнвентарь, маркетинг, аналитика, AI-менеджер, лиды и биллинг.",
        "uk": "🚘 Автомобілі\n\nІнвентар, маркетинг, аналітика, AI-менеджер, ліди та білінг.",
    },
    "auto_quick_actions": {"ru": "Быстрые действия:", "uk": "Швидкі дії:"},
    "auto_no_access": {
        "ru": "🚗 Авто\n\nНет доступа к модулю.",
        "uk": "🚗 Авто\n\nНемає доступу до модуля.",
    },
    "auto_unavailable": {
        "ru": "Автомобильный модуль временно недоступен.",
        "uk": "Автомобільний модуль тимчасово недоступний.",
    },
    "main_menu": {"ru": "Главное меню", "uk": "Головне меню"},
    "partner_cards": {"ru": "Карточки партнёров:", "uk": "Картки партнерів:"},
    "no_partners": {
        "ru": "Партнёры пока не настроены.",
        "uk": "Партнери поки не налаштовані.",
    },
    "choose_car": {"ru": "Выберите автомобиль:", "uk": "Оберіть автомобіль:"},
    "back_inline": {"ru": "⬅ Назад", "uk": "⬅ Назад"},
    "back_partners": {"ru": "⬅ К партнёрам", "uk": "⬅ До партнерів"},
}

_AUTO_BUTTONS: dict[str, dict[str, str]] = {
    "main": {"ru": "🚗 Авто", "uk": "🚗 Авто"},
    "hub_cars": {"ru": "🚘 Автомобили", "uk": "🚘 Автомобілі"},
    "hub_insurance": {"ru": "🛡 Страхование", "uk": "🛡 Страхування"},
    "hub_credit": {"ru": "🏦 Кредит", "uk": "🏦 Кредит"},
    "hub_leasing": {"ru": "💳 Лизинг", "uk": "💳 Лізинг"},
    "hub_logistics": {"ru": "🚚 Логистика", "uk": "🚚 Логістика"},
    "hub_legal": {"ru": "⚖ Юридическая поддержка", "uk": "⚖ Юридична підтримка"},
    "back": {"ru": "⬅ Назад", "uk": "⬅ Назад"},
    "back_to_hub": {"ru": "⬅ К авто", "uk": "⬅ До авто"},
    "add_car": {"ru": "🚗 Добавить авто", "uk": "🚗 Додати авто"},
    "list_cars": {"ru": "📋 Список авто", "uk": "📋 Список авто"},
    "search_car": {"ru": "🔍 Поиск авто", "uk": "🔍 Пошук авто"},
    "profit_calc": {"ru": "💰 Калькулятор прибыли", "uk": "💰 Калькулятор прибутку"},
    "marketing": {"ru": "📢 Продвижение", "uk": "📢 Просування"},
    "analytics": {"ru": "📊 Аналитика", "uk": "📊 Аналітика"},
    "ai_manager": {"ru": "🤖 AI Менеджер", "uk": "🤖 AI Менеджер"},
    "leads": {"ru": "👥 Лиды", "uk": "👥 Ліди"},
    "billing": {"ru": "💳 Тарифы и услуги", "uk": "💳 Тарифи та послуги"},
    "dealer_rates": {"ru": "💱 Курсы дилера", "uk": "💱 Курси дилера"},
    "treasury": {"ru": "🏦 Казначейство", "uk": "🏦 Казначейство"},
    "auto_settings": {"ru": "⚙ Настройки авто", "uk": "⚙ Налаштування авто"},
}

_CATEGORY_HEADERS: dict[str, dict[str, str]] = {
    "INSURANCE": {"ru": "🛡 Страхование", "uk": "🛡 Страхування"},
    "CREDIT": {"ru": "🏦 Кредит", "uk": "🏦 Кредит"},
    "LEASING": {"ru": "💳 Лизинг", "uk": "💳 Лізинг"},
    "LOGISTICS": {"ru": "🚚 Логистика", "uk": "🚚 Логістика"},
    "LEGAL": {"ru": "⚖ Юридическая поддержка", "uk": "⚖ Юридична підтримка"},
}

_HUB_KEY_TO_CATEGORY = {
    "hub_insurance": "INSURANCE",
    "hub_credit": "CREDIT",
    "hub_leasing": "LEASING",
    "hub_logistics": "LOGISTICS",
    "hub_legal": "LEGAL",
}

_AUTO_ROLES: dict[str, dict[str, str]] = {
    "buyer": {"ru": "👤 Покупатель", "uk": "👤 Покупець"},
    "seller": {"ru": "💰 Продавец", "uk": "💰 Продавець"},
    "dealer": {"ru": "🏢 Дилер", "uk": "🏢 Дилер"},
    "marketplace": {"ru": "🚘 Автоплощадка", "uk": "🚘 Автоплощадка"},
    "partner": {"ru": "🤝 Партнер", "uk": "🤝 Партнер"},
    "insurance": {"ru": "🛡 Страховая компания", "uk": "🛡 Страхова компанія"},
    "bank": {"ru": "🏦 Банк", "uk": "🏦 Банк"},
    "logistics": {"ru": "🚚 Логистика", "uk": "🚚 Логістика"},
    "legal_partner": {"ru": "⚖ Юридический партнер", "uk": "⚖ Юридичний партнер"},
    "service_station": {"ru": "🔧 СТО", "uk": "🔧 СТО"},
    "parts_store": {"ru": "📦 Магазин запчастей", "uk": "📦 Магазин запчастин"},
}

_LEGACY_ALIASES = {
    "🚗 Auto": "main",
    "🚗 Cars": "hub_cars",
    "🚘 Cars": "hub_cars",
    "🛡 Insurance": "hub_insurance",
    "🏦 Credit": "hub_credit",
    "💳 Leasing": "hub_leasing",
    "🚚 Logistics": "hub_logistics",
    "⚖ Legal": "hub_legal",
    "⬅ К Auto": "back_to_hub",
    "➕ Add Car": "add_car",
    "📋 Car List": "list_cars",
    "🔎 Search Car": "search_car",
    "🧮 Profit Calculator": "profit_calc",
    "📣 Marketing": "marketing",
    "🏦 Treasury Dashboard": "treasury",
}


def normalize_language(language: str | None) -> str:
    if language and language.lower() in SUPPORTED_LANGUAGES:
        return language.lower()
    return DEFAULT_LANGUAGE


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    language = normalize_language(lang)
    bucket = _TEXTS.get(key) or _AUTO_BUTTONS.get(key) or _AUTO_ROLES.get(key) or {}
    text = bucket.get(language) or bucket.get(DEFAULT_LANGUAGE) or key
    if kwargs:
        return text.format(**kwargs)
    return text


def btn(key: str, lang: str | None = None) -> str:
    language = normalize_language(lang)
    labels = _AUTO_BUTTONS.get(key, {})
    return labels.get(language) or labels.get(DEFAULT_LANGUAGE) or key


def role_label(role_code: str, lang: str | None = None) -> str:
    language = normalize_language(lang)
    labels = _AUTO_ROLES.get(role_code, {})
    return labels.get(language) or labels.get(DEFAULT_LANGUAGE) or role_code


def category_header(category: str, lang: str | None = None) -> str:
    language = normalize_language(lang)
    labels = _CATEGORY_HEADERS.get(category, {})
    return labels.get(language) or labels.get(DEFAULT_LANGUAGE) or category


def resolve_auto_screen(text: str | None) -> str | None:
    if not text:
        return None
    stripped = text.strip()
    if stripped in _LEGACY_ALIASES:
        return _LEGACY_ALIASES[stripped]
    for key, labels in _AUTO_BUTTONS.items():
        if stripped in labels.values():
            return key
    return None


def all_auto_button_labels() -> frozenset[str]:
    labels: set[str] = set(_LEGACY_ALIASES.keys())
    for bucket in _AUTO_BUTTONS.values():
        labels.update(bucket.values())
    return frozenset(labels)


def hub_screen_to_category(screen_key: str | None) -> str | None:
    if screen_key is None:
        return None
    return _HUB_KEY_TO_CATEGORY.get(screen_key)


def all_role_labels() -> frozenset[str]:
    labels: set[str] = set()
    for bucket in _AUTO_ROLES.values():
        labels.update(bucket.values())
    return frozenset(labels)


def role_code_from_label(text: str) -> str | None:
    stripped = text.strip()
    for code, labels in _AUTO_ROLES.items():
        if stripped in labels.values():
            return code
    return None
