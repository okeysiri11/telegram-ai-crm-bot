# Entry point routing — strict start-command flows and navigation guards.

from __future__ import annotations

from enum import StrEnum

from services.automotive_localization import btn


class EntryPoint(StrEnum):
    AUTO_CLIENT = "AUTO_CLIENT"
    AUTO_DEALER = "AUTO_DEALER"
    AGRO_CLIENT = "AGRO_CLIENT"
    AGRO_SUPPLIER = "AGRO_SUPPLIER"
    OWNER = "OWNER"


class FlowState(StrEnum):
    LANGUAGE_SELECT = "LANGUAGE_SELECT"
    AUTO_CLIENT_MENU = "AUTO_CLIENT_MENU"
    DEALER_TYPE_SELECT = "DEALER_TYPE_SELECT"
    PLAN_SELECT = "PLAN_SELECT"
    PAYMENT = "PAYMENT"
    AGRO_CLIENT_MENU = "AGRO_CLIENT_MENU"
    AGRO_SUPPLIER_MENU = "AGRO_SUPPLIER_MENU"
    OWNER_DASHBOARD = "OWNER_DASHBOARD"


SOURCE_LINK_TO_ENTRY_POINT: dict[str, EntryPoint] = {
    "auto_client": EntryPoint.AUTO_CLIENT,
    "auto_dealer": EntryPoint.AUTO_DEALER,
    "agro": EntryPoint.AGRO_CLIENT,
    "agro_farmer": EntryPoint.AGRO_CLIENT,
    "agro_supplier": EntryPoint.AGRO_SUPPLIER,
}

ENTRY_POINT_INITIAL_STATE: dict[EntryPoint, FlowState] = {
    EntryPoint.AUTO_CLIENT: FlowState.LANGUAGE_SELECT,
    EntryPoint.AUTO_DEALER: FlowState.LANGUAGE_SELECT,
    EntryPoint.AGRO_CLIENT: FlowState.LANGUAGE_SELECT,
    EntryPoint.AGRO_SUPPLIER: FlowState.LANGUAGE_SELECT,
    EntryPoint.OWNER: FlowState.OWNER_DASHBOARD,
}

ENTRY_POINT_POST_LANGUAGE_STATE: dict[EntryPoint, FlowState] = {
    EntryPoint.AUTO_CLIENT: FlowState.AUTO_CLIENT_MENU,
    EntryPoint.AUTO_DEALER: FlowState.DEALER_TYPE_SELECT,
    EntryPoint.AGRO_CLIENT: FlowState.AGRO_CLIENT_MENU,
    EntryPoint.AGRO_SUPPLIER: FlowState.AGRO_SUPPLIER_MENU,
    EntryPoint.OWNER: FlowState.OWNER_DASHBOARD,
}

FLOW_STATE_TO_ENTRY_POINT: dict[FlowState, EntryPoint] = {
    FlowState.AUTO_CLIENT_MENU: EntryPoint.AUTO_CLIENT,
    FlowState.DEALER_TYPE_SELECT: EntryPoint.AUTO_DEALER,
    FlowState.PLAN_SELECT: EntryPoint.AUTO_DEALER,
    FlowState.PAYMENT: EntryPoint.AUTO_DEALER,
    FlowState.AGRO_CLIENT_MENU: EntryPoint.AGRO_CLIENT,
    FlowState.AGRO_SUPPLIER_MENU: EntryPoint.AGRO_SUPPLIER,
    FlowState.OWNER_DASHBOARD: EntryPoint.OWNER,
}

# command → router → flow → first_state
START_ROUTE_TABLE: list[dict[str, str]] = [
    {
        "command": "/start_auto_client",
        "router": "start_routing_handlers",
        "flow": EntryPoint.AUTO_CLIENT,
        "first_state": FlowState.LANGUAGE_SELECT,
    },
    {
        "command": "/start auto_client",
        "router": "start_routing_handlers",
        "flow": EntryPoint.AUTO_CLIENT,
        "first_state": FlowState.LANGUAGE_SELECT,
    },
    {
        "command": "/start_auto_dealer",
        "router": "start_routing_handlers",
        "flow": EntryPoint.AUTO_DEALER,
        "first_state": FlowState.LANGUAGE_SELECT,
    },
    {
        "command": "/start auto_dealer",
        "router": "start_routing_handlers",
        "flow": EntryPoint.AUTO_DEALER,
        "first_state": FlowState.LANGUAGE_SELECT,
    },
    {
        "command": "/start (owner)",
        "router": "start_routing_handlers",
        "flow": EntryPoint.OWNER,
        "first_state": FlowState.OWNER_DASHBOARD,
    },
    {
        "command": "/start (regular user)",
        "router": "start_routing_handlers",
        "flow": "—",
        "first_state": FlowState.LANGUAGE_SELECT,
    },
]

_AUTO_CLIENT_MENU_KEYS = (
    "client_buy_car",
    "client_sell_car",
    "client_listing",
    "client_services",
    "client_manager",
)

ECOSYSTEM_MENU_BUTTONS = frozenset({
    "💰 Crypto OTC",
    "🚁 Drone Engineering",
    "⚖ Юриспруденция",
    "☕ Cafe & Beauty",
    "🌾 Agro Trading",
    "🏢 Company Core",
    "🚗 Авто",
    "👥 Пользователи",
    "📅 Календарь",
    "📊 Аналитика",
    "🤖 AI Агенты",
    "🤖 AI помощник",
    "🔔 Уведомления",
    "✅ Задачи",
    "📂 Файлы",
    "🔎 Поиск",
    "📊 Отчеты",
    "📁 Файлы и документы",
    "🔎 Глобальный поиск",
    "⚙️ Бизнес-процессы",
    "⚙ Администрирование",
    "👑 Owner Panel",
    "🤝 Partner Cabinet",
    "📊 Owner Dashboard",
    "🧪 Тестовый центр",
    "❤️ System Health",
    "🏠 Мой раздел",
})

DEALER_ONBOARDING_CALLBACK_PREFIXES = (
    "onboard:automotive",
    "onboard:resume",
    "onboard:analytics",
    "billing:",
    "payment:",
)


def auto_client_menu_labels(lang: str | None = None) -> frozenset[str]:
    return frozenset(btn(key, lang) for key in _AUTO_CLIENT_MENU_KEYS)


def is_auto_client_menu_text(text: str | None, lang: str | None = None) -> bool:
    if not text:
        return False
    normalized = text.strip()
    for check_lang in (lang, "ru", "uk"):
        if normalized in auto_client_menu_labels(check_lang):
            return True
    return False


def flow_for_dealer_step(step: str | None) -> FlowState | None:
    if step in {None, "started", "STARTED"}:
        return FlowState.DEALER_TYPE_SELECT
    if step in {"automotive_selected", "AUTOMOTIVE_SELECTED"}:
        return FlowState.PLAN_SELECT
    if step in {
        "tariff_selected",
        "pricing_model_selected",
        "payment_created",
        "TARIFF_SELECTED",
        "PRICING_MODEL_SELECTED",
        "PAYMENT_CREATED",
    }:
        return FlowState.PAYMENT
    return None
