# Tenant deep-link routing — entry points, scoped navigation, link registry seed.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import OWNER_ID

TENANT_ENTRY_LINK_CODES = frozenset({
    "auto_client",
    "auto_dealer",
    "agro",
    "drones",
    "legal",
    "insurance_partner",
    "finance_partner",
    "service_partner",
})

# Legacy vertical-only deep links still accepted for owner/testing.
LEGACY_VERTICAL_LINKS = frozenset({
    "auto",
    "finance",
    "crypto",
    "cafe",
    "beauty",
})

ALL_DEEP_LINK_CODES = TENANT_ENTRY_LINK_CODES | LEGACY_VERTICAL_LINKS


@dataclass(frozen=True)
class TenantEntryConfig:
    code: str
    tenant_code: str
    vertical: str
    title_ru: str
    title_uk: str
    preset_role: str | None = None
    entry_target: str | None = None  # hub section key for auto partners
    skip_role_picker: bool = True


ENTRY_LINK_REGISTRY: dict[str, TenantEntryConfig] = {
    "auto_client": TenantEntryConfig(
        code="auto_client",
        tenant_code="auto_client",
        vertical="auto",
        title_ru="🚗 Авто — клиент",
        title_uk="🚗 Авто — клієнт",
        preset_role="buyer",
        entry_target="hub_cars",
    ),
    "auto_dealer": TenantEntryConfig(
        code="auto_dealer",
        tenant_code="auto_dealer",
        vertical="auto",
        title_ru="🏢 Авто — дилер",
        title_uk="🏢 Авто — дилер",
        preset_role="dealer",
        entry_target="hub_cars",
    ),
    "agro": TenantEntryConfig(
        code="agro",
        tenant_code="agro",
        vertical="agro",
        title_ru="🌾 Agro Trading",
        title_uk="🌾 Agro Trading",
    ),
    "drones": TenantEntryConfig(
        code="drones",
        tenant_code="drones",
        vertical="drones",
        title_ru="🚁 Drone Engineering",
        title_uk="🚁 Drone Engineering",
    ),
    "legal": TenantEntryConfig(
        code="legal",
        tenant_code="legal",
        vertical="legal",
        title_ru="⚖ Юриспруденция",
        title_uk="⚖ Юриспруденция",
    ),
    "insurance_partner": TenantEntryConfig(
        code="insurance_partner",
        tenant_code="insurance_partner",
        vertical="auto",
        title_ru="🛡 Страховой партнёр",
        title_uk="🛡 Страховий партнер",
        preset_role="insurance",
        entry_target="hub_insurance",
    ),
    "finance_partner": TenantEntryConfig(
        code="finance_partner",
        tenant_code="finance_partner",
        vertical="auto",
        title_ru="🏦 Финансовый партнёр",
        title_uk="🏦 Фінансовий партнер",
        preset_role="bank",
        entry_target="hub_credit",
    ),
    "service_partner": TenantEntryConfig(
        code="service_partner",
        tenant_code="service_partner",
        vertical="auto",
        title_ru="🔧 Сервисный партнёр",
        title_uk="🔧 Сервісний партнер",
        preset_role="service_station",
        entry_target="hub_cars",
    ),
}

TENANT_ALLOWED_MODULES: dict[str, frozenset[str]] = {
    "auto_client": frozenset({"auto", "settings"}),
    "auto_dealer": frozenset({"auto", "settings"}),
    "agro": frozenset({"agro", "settings"}),
    "drones": frozenset({"drones", "settings"}),
    "legal": frozenset({"legal", "settings"}),
    "insurance_partner": frozenset({"auto", "settings"}),
    "finance_partner": frozenset({"auto", "settings"}),
    "service_partner": frozenset({"auto", "settings"}),
}

VERTICAL_TO_MODULE: dict[str, str] = {
    "auto": "auto",
    "agro": "agro",
    "drones": "drones",
    "legal": "legal",
    "finance": "crypto",
    "crypto": "crypto",
    "cafe": "cafe_beauty",
    "beauty": "cafe_beauty",
}


def parse_entry_link(args: str | None) -> TenantEntryConfig | None:
    if not args:
        return None
    code = args.strip().lower().split()[0]
    if code in ENTRY_LINK_REGISTRY:
        return ENTRY_LINK_REGISTRY[code]
    return None


def legacy_vertical_from_args(args: str | None) -> str | None:
    if not args:
        return None
    code = args.strip().lower().split()[0]
    if code in LEGACY_VERTICAL_LINKS:
        return code
    return None


def format_deeplink_url(bot_username: str, code: str) -> str:
    username = bot_username.lstrip("@")
    return f"https://t.me/{username}?start={code}"


def entry_link_seed_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, cfg in enumerate(ENTRY_LINK_REGISTRY.values()):
        rows.append(
            {
                "code": cfg.code,
                "tenant_code": cfg.tenant_code,
                "vertical": cfg.vertical,
                "title_ru": cfg.title_ru,
                "title_uk": cfg.title_uk,
                "preset_role": cfg.preset_role,
                "entry_target": cfg.entry_target,
                "sort_order": idx,
                "is_active": True,
            }
        )
    return rows


def module_for_button_text(text: str | None) -> str | None:
    if not text:
        return None
    mapping = {
        "💰 Crypto OTC": "crypto",
        "🚁 Drone Engineering": "drones",
        "⚖ Юриспруденция": "legal",
        "☕ Cafe & Beauty": "cafe_beauty",
        "🌾 Agro Trading": "agro",
        "🏢 Company Core": "company",
        "🚗 Авто": "auto",
        "👥 Пользователи": "users",
        "📅 Календарь": "calendar",
        "📊 Аналитика": "dashboard",
        "🤖 AI Агенты": "ai_agents",
        "🤖 AI помощник": "ai_assistant",
        "🔔 Уведомления": "notifications",
        "✅ Задачи": "tasks",
        "📂 Файлы": "files",
        "🔎 Поиск": "search",
        "📊 Отчеты": "reports",
        "📁 Файлы и документы": "files_docs",
        "🔎 Глобальный поиск": "global_search",
        "⚙️ Бизнес-процессы": "workflow",
        "⚙ Администрирование": "admin",
        "⚙ Настройки": "settings",
        "⚙ Налаштування": "settings",
        "🧪 Тестовый центр": "test_center",
        "❤️ System Health": "system_health",
        "👑 Owner Panel": "owner_panel",
    }
    return mapping.get(text.strip())


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID
