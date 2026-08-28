"""Unified Menu Catalog — Sprint 34.2B.
One catalog · many client renderers (Web sidebar, Telegram keyboards, Mobile, Desktop).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_registry.visibility import DEFAULT_UI_CLIENTS, ClientId


@dataclass
class MenuItem:
    id: str
    title: str
    icon: str
    route: str | None = None
    telegram_command: str | None = None
    required_permissions: tuple[str, ...] = ()
    required_roles: tuple[str, ...] = ()
    required_workspace: str | None = None
    required_vertical: str | None = None
    client_visibility: tuple[str, ...] = DEFAULT_UI_CLIENTS
    feature_flags: tuple[str, ...] = ()
    children: list["MenuItem"] = field(default_factory=list)
    group: str | None = None
    simple: bool = False
    owner_only: bool = False
    title_en: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "title_en": self.title_en or self.title,
            "icon": self.icon,
            "route": self.route,
            "telegram_command": self.telegram_command,
            "required_permissions": list(self.required_permissions),
            "required_roles": list(self.required_roles),
            "required_workspace": self.required_workspace,
            "required_vertical": self.required_vertical,
            "client_visibility": list(self.client_visibility),
            "feature_flags": list(self.feature_flags),
            "group": self.group,
            "simple": self.simple,
            "owner_only": self.owner_only,
            "children": [c.to_dict() for c in self.children],
        }


def _item(
    id: str,
    title: str,
    icon: str,
    route: str | None = None,
    *,
    tg: str | None = None,
    perms: tuple[str, ...] = (),
    roles: tuple[str, ...] = (),
    group: str | None = None,
    simple: bool = False,
    owner_only: bool = False,
    vertical: str | None = None,
    workspace: str | None = None,
    clients: tuple[str, ...] = DEFAULT_UI_CLIENTS,
    title_en: str | None = None,
    children: list[MenuItem] | None = None,
) -> MenuItem:
    return MenuItem(
        id=id,
        title=title,
        title_en=title_en,
        icon=icon,
        route=route,
        telegram_command=tg,
        required_permissions=perms,
        required_roles=roles,
        required_workspace=workspace,
        required_vertical=vertical,
        client_visibility=clients,
        group=group,
        simple=simple,
        owner_only=owner_only,
        children=children or [],
    )


WEB_DESKTOP_MOBILE = (
    ClientId.WEB.value,
    ClientId.DESKTOP.value,
    ClientId.MOBILE.value,
    ClientId.API.value,
)

# Canonical menu catalog — single source of truth for all clients.
MENU_CATALOG: list[MenuItem] = [
    # Workspace
    _item("ws_home", "Главная", "dashboard", "/dashboard", tg="home", group="workspace", simple=True, title_en="Home"),
    _item("ws_desktop", "Рабочий стол", "desktop", "/desktop", tg="desktop", group="workspace", simple=True, title_en="Desktop"),
    _item("ws_calendar", "Календарь", "calendar", "/calendar", tg="📅 Календарь", perms=("calendar.read",), group="workspace", simple=True, title_en="Calendar"),
    _item("ws_tasks", "Задачи", "tasks", "/tasks", tg="✅ Задачи", perms=("tasks.read",), group="workspace", simple=True, title_en="Tasks"),
    _item("ws_documents", "Документы", "documents", "/documents", tg="documents", perms=("documents.manage", "files.upload"), group="workspace", simple=True, title_en="Documents"),
    _item("ws_notifications", "Уведомления", "bell", "/notifications", tg="🔔 Уведомления", group="workspace", simple=True, title_en="Notifications"),
    _item("ws_settings", "Настройки", "settings", "/settings", tg="⚙ Настройки", group="workspace", simple=True, title_en="Settings"),
    _item("ws_search", "Поиск", "search", "/search", tg="search", group="workspace", simple=True, title_en="Search"),
    # Business
    _item("biz_crm", "CRM", "crm", "/crm", tg="crm", perms=("crm.read",), group="business", simple=True, workspace="crm"),
    _item("biz_clients", "Клиенты", "crm", "/crm?view=clients", tg="clients", perms=("crm.read",), group="business", simple=True, title_en="Clients"),
    _item("biz_projects", "Проекты", "projects", "/projects", tg="projects", perms=("tasks.read",), group="business", simple=True, title_en="Projects"),
    _item("biz_finance", "Финансы", "finance", "/analytics", tg="finance", perms=("analytics.read",), group="business", simple=True, title_en="Finance", workspace="finance"),
    _item("biz_erp", "ERP", "erp", "/erp", tg="erp", perms=("erp.read",), group="business", workspace="erp"),
    _item("biz_mfg", "Производство", "factory", "/erp?view=production", tg="manufacturing", perms=("erp.read",), group="business", vertical="manufacturing", title_en="Manufacturing"),
    _item("biz_marketplace", "Маркетплейс", "marketplace", "/marketplace", tg="marketplace", perms=("crm.read",), group="business", workspace="marketplace", title_en="Marketplace"),
    _item("biz_legal", "Юридический отдел", "legal", "/workspace/legal", tg="legal", perms=("knowledge.read",), group="business", vertical="legal", title_en="Legal"),
    _item("biz_analytics", "Аналитика", "analytics", "/analytics", tg="📊 Аналитика", perms=("analytics.read",), group="business", workspace="analytics", title_en="Analytics"),
    # AI
    _item("ai_agents", "AI-Ассистент", "ai", "/ai-agents", tg="🤖 AI Агенты", perms=("ai.use", "agent.execute"), group="ai", simple=True, title_en="AI Assistant"),
    _item("ai_helper", "AI помощник", "ai", "/ai-agents", tg="🤖 AI помощник", perms=("ai.use",), group="ai", simple=True, title_en="AI Helper"),
    _item("ai_studio", "Студия AI", "ai", "/ai-studio", tg="🎨 AI Studio", perms=("studio.generate",), group="ai", workspace="ai_studio", title_en="AI Studio"),
    _item("ai_production", "Продакшн", "production", "/production-studio", tg="production", perms=("studio.generate",), group="ai", workspace="production", title_en="Production"),
    _item("ai_knowledge", "Знания", "knowledge", "/knowledge", tg="knowledge", perms=("knowledge.read",), group="ai", workspace="knowledge", title_en="Knowledge"),
    _item("ai_runtime", "Среда AI", "ai", "/platform-builder/ai-runtime", tg="ai_runtime", perms=("agent.execute",), group="ai", title_en="AI Runtime"),
    _item("context_engine", "Движок контекста", "ai", "/platform-builder/context-engine", tg="context_engine", perms=("agent.execute",), group="ai", title_en="Context Engine"),
    _item("project_memory", "Память проектов", "ai", "/platform-builder/project-memory", tg="project_memory", perms=("agent.execute",), group="ai", title_en="Project Memory"),
    _item("voice_runtime", "Голосовая среда", "ai", "/platform-builder/voice", tg="voice", perms=("agent.execute",), group="ai", title_en="Voice Runtime"),
    _item("multi_agent", "Мульти-агентная среда", "ai", "/platform-builder/multi-agent", tg="multi_agent", perms=("agent.execute",), group="ai", title_en="Multi-Agent Runtime"),
    _item("skills_sdk", "Навыки AI и SDK", "ai", "/platform-builder/skills", tg="skills", perms=("agent.execute",), group="ai", title_en="AI Skills & SDK"),
    _item("creative_factory", "Креативная фабрика", "ai", "/platform-builder/creative", tg="creative", perms=("agent.execute",), group="ai", title_en="Creative Factory"),
    _item("enterprise_city_runtime", "Среда города", "analytics", "/platform", tg="platform", perms=("agent.execute",), group="platform", title_en="Enterprise City Runtime"),
    _item("ai_team", "Команда AI", "ai", "/platform-builder/ai-team", tg="ai_team", perms=("agent.execute",), group="ai", title_en="AI Team"),
    # City
    _item("city_map", "Корпоративный город", "city", "/enterprise-city", tg="city", group="city", title_en="Enterprise City"),
    _item("city_control", "Диспетчерская", "city", "/control-tower", tg="control_tower", group="city", roles=("owner", "administrator", "ceo"), title_en="Control Tower"),
    # Platform
    _item("plat_builder", "Конструктор платформы", "builder", "/platform-builder", tg="platform_builder", perms=("platform.config.read",), group="platform", roles=("owner", "administrator", "ceo"), title_en="Platform Builder"),
    _item("plat_service_builder", "Конструктор сервисов", "builder", "/platform-builder/service-builder", tg="service_builder", perms=("platform.config.read",), group="platform", roles=("owner", "administrator", "ceo"), title_en="Service Builder"),
    _item("plat_event_bus", "Шина событий", "zap", "/platform-builder/event-bus", tg="event_bus", perms=("platform.config.read",), group="platform", roles=("owner", "administrator", "ceo"), title_en="Event Bus"),
    _item("plat_workflows", "Сценарии", "workflow", "/platform-builder/workflows", tg="workflows", perms=("platform.config.read",), group="platform", roles=("owner", "administrator", "ceo"), title_en="Workflows"),
    _item("plat_integrations", "Интеграции", "integrations", "/platform-builder/integrations", tg="integrations", perms=("platform.config.read",), group="platform", workspace="integrations", title_en="Integrations"),
    _item("plat_security", "Безопасность", "security", "/identity/security", tg="security", perms=("admin.manage",), group="platform", roles=("owner", "administrator"), title_en="Security"),
    _item("plat_health", "Здоровье платформы", "health", "/health", tg="health", group="platform", title_en="Platform Health"),
    _item("ai_concierge", "AI Консьерж", "ai", "/ai-agents", tg="🤖 AI Консьерж", perms=("ai.use",), group="ai", simple=True, title_en="AI Concierge"),
    _item("tg_dashboard", "Дашборд", "dashboard", "/dashboard", tg="📊 Дашборд", group="workspace", simple=True, title_en="Dashboard"),
    _item("tg_tasks", "Задачи", "tasks", "/tasks", tg="📋 Задачи", perms=("tasks.read",), group="workspace", simple=True, title_en="Tasks"),
    _item("tg_business", "Бизнес", "crm", "/crm", tg="🏢 Бизнес", group="business", simple=True, title_en="Business"),
    _item("tg_all_sections", "Все разделы", "apps", "/desktop", tg="📂 Все разделы", group="workspace", simple=True, title_en="All sections"),
    _item("tg_developer", "Developer Tools", "settings", "/platform-builder", tg="⚙ Developer Tools", perms=("platform.config.read",), group="platform", roles=("owner", "administrator", "developer"), owner_only=True, title_en="Developer Tools"),
    # Verticals
    _item(
        "vert_auto", "Авто", "auto", "/workspace/auto", tg="🚗 Авто", perms=("crm.read",), group="verticals", vertical="auto", title_en="Automotive",
        children=[
            _item("vert_auto_cars", "Автомобили", "auto", "/workspace/auto/cars", vertical="auto"),
            _item("vert_auto_insurance", "Страхование", "shield", "/workspace/auto/insurance", vertical="auto"),
            _item("vert_auto_credit", "Кредит", "finance", "/workspace/auto/credit", vertical="auto"),
            _item("vert_auto_leasing", "Лизинг", "finance", "/workspace/auto/leasing", vertical="auto"),
            _item("vert_auto_logistics", "Логистика", "logistics", "/workspace/auto/logistics", vertical="auto"),
            _item("vert_auto_legal", "Юридическая поддержка", "legal", "/workspace/auto/legal", vertical="auto"),
        ],
    ),
    _item("vert_crypto", "Crypto OTC", "crypto", "/workspace/crypto", tg="💰 Crypto OTC", perms=("crm.read",), group="verticals", vertical="crypto_otc"),
    _item("vert_drone", "Drone", "drone", "/workspace/drone", tg="🚁 Drone Engineering", perms=("crm.read",), group="verticals", vertical="drone"),
    _item(
        "vert_agro", "Агро", "agro", "/workspace/agro", tg="🌾 Agro Trading", perms=("crm.read",), group="verticals", vertical="agro",
        children=[
            _item("vert_agro_goods", "Товары (закупка / продажа)", "marketplace", "/workspace/agro/goods", vertical="agro"),
            _item("vert_agro_counterparties", "Контрагенты", "users", "/workspace/agro/counterparties", vertical="agro"),
            _item("vert_agro_contracts", "Контракты", "documents", "/workspace/agro/contracts", vertical="agro"),
            _item("vert_agro_deals", "Сделки", "deals", "/workspace/agro/deals", vertical="agro"),
            _item("vert_agro_logistics", "Логистика", "logistics", "/workspace/agro/logistics", vertical="agro"),
        ],
    ),
    _item("vert_cafe", "Cafe", "cafe", "/workspace/cafe", tg="☕ Cafe", perms=("crm.read",), group="verticals", vertical="cafe_beauty"),
    _item(
        "vert_beauty", "Beauty", "beauty", "/workspace/beauty", tg="💄 Beauty", perms=("crm.read",), group="verticals", vertical="beauty", title_en="Beauty",
        children=[
            _item("vert_beauty_salon", "Салон", "beauty", "/workspace/beauty/salon", vertical="beauty"),
            _item("vert_beauty_clients", "Клиенты", "users", "/workspace/beauty/clients", vertical="beauty"),
            _item("vert_beauty_appointments", "Записи", "calendar", "/workspace/beauty/appointments", vertical="beauty"),
            _item("vert_beauty_calendar", "Календарь", "calendar", "/workspace/beauty/calendar", vertical="beauty"),
        ],
    ),
    _item("vert_casino", "Casino", "marketplace", "/casino", tg=None, perms=("crm.read",), group="verticals", title_en="Casino", simple=True),
    _item("vert_legal", "Legal", "legal", "/workspace/legal", tg="⚖ Юриспруденция", perms=("knowledge.read",), group="verticals", vertical="legal"),
    _item("vert_company", "Company Core", "building", "/workspace/company-core", tg="🏢 Company Core", group="verticals", vertical="company_core", roles=("owner", "administrator", "manager", "ceo")),
    _item("vert_construction", "Construction", "construction", "/workspace/construction", tg=None, group="verticals", vertical="construction", clients=WEB_DESKTOP_MOBILE),
    _item("vert_medical", "Medical", "medical", "/workspace/medical", tg=None, group="verticals", vertical="medical", clients=WEB_DESKTOP_MOBILE),
    _item("vert_mfg", "Manufacturing", "factory", "/erp?view=production", tg=None, group="verticals", vertical="manufacturing", clients=WEB_DESKTOP_MOBILE),
    # Owner
    _item("own_dashboard", "Owner Dashboard", "dashboard", "/owner", tg="📊 Owner Dashboard", group="owner", owner_only=True, roles=("owner", "ceo")),
    _item("own_panel", "Owner Panel", "settings", "/owner", tg="⚙️ Owner Panel", group="owner", owner_only=True, roles=("owner",)),
    _item("own_god", "God Mode", "security", "/platform-builder/god-mode", tg="god_mode", group="owner", owner_only=True, roles=("owner",), perms=("owner.full_access",)),
]

MENU_GROUPS: dict[str, dict[str, str]] = {
    "workspace": {"label": "Рабочее пространство", "label_en": "Workspace", "icon": "desktop"},
    "business": {"label": "Бизнес", "label_en": "Business", "icon": "crm"},
    "ai": {"label": "AI", "label_en": "AI", "icon": "ai"},
    "city": {"label": "Enterprise City", "label_en": "Enterprise City", "icon": "city"},
    "platform": {"label": "Платформа", "label_en": "Platform", "icon": "builder"},
    "verticals": {"label": "Вертикали", "label_en": "Verticals", "icon": "apps"},
    "owner": {"label": "Владелец", "label_en": "Owner", "icon": "dashboard"},
}


def all_menu_items() -> list[MenuItem]:
    return list(MENU_CATALOG)


def menu_item_by_id(item_id: str) -> MenuItem | None:
    for item in MENU_CATALOG:
        if item.id == item_id:
            return item
    return None
