"""Register all framework-ready vertical configs."""

from __future__ import annotations

from platform_vertical_ai.configs.beauty import BEAUTY_CONFIG
from platform_vertical_ai.configs.skeleton import _skeleton
from platform_vertical_ai.models import VerticalConfig

# Framework-ready industry list (Sprint 43.4). Beauty is complete; others are config skeletons.
VERTICAL_CONFIGS: dict[str, VerticalConfig] = {
    "beauty": BEAUTY_CONFIG,
    "auto": _skeleton(
        vid="auto",
        name_ru="Авто",
        icon="🚗",
        color="#3B82F6",
        description_ru="Автобизнес: объявления, Reels, маркетплейсы.",
        scenarios=("Объявление", "Reels автосалона", "Тест-драйв", "Акция", "Trade-in"),
    ),
    "construction": _skeleton(
        vid="construction",
        name_ru="Строительство",
        icon="🏗",
        color="#F59E0B",
        description_ru="Строительство: баннеры, КП, портфолио объектов.",
    ),
    "legal": _skeleton(
        vid="legal",
        name_ru="Юридические услуги",
        icon="⚖",
        color="#6366F1",
        description_ru="Юриспруденция: договоры, письма, претензии.",
        scenarios=("Договор", "Претензия", "Письмо", "Анализ документа"),
    ),
    "crypto": _skeleton(
        vid="crypto",
        name_ru="Crypto OTC",
        icon="💰",
        color="#10B981",
        description_ru="Crypto OTC: аналитика, посты, предложения.",
    ),
    "agro": _skeleton(
        vid="agro",
        name_ru="Агро",
        icon="🌾",
        color="#84CC16",
        description_ru="Агро: КП, цены, презентации.",
    ),
    "travel": _skeleton(
        vid="travel",
        name_ru="Туризм",
        icon="✈",
        color="#06B6D4",
        description_ru="Туризм: туры, сторис, реклама направлений.",
    ),
    "production": _skeleton(
        vid="production",
        name_ru="Производство",
        icon="🏭",
        color="#64748B",
        description_ru="Производство: презентации, каталоги, B2B.",
    ),
    "manufacturing": _skeleton(
        vid="manufacturing",
        name_ru="Manufacturing",
        icon="⚙",
        color="#475569",
        description_ru="Manufacturing: оборудование, B2B маркетинг.",
    ),
    "cafe": _skeleton(
        vid="cafe",
        name_ru="Кафе",
        icon="☕",
        color="#D97706",
        description_ru="Кафе и рестораны: меню, акции, сторис.",
    ),
    "medical": _skeleton(
        vid="medical",
        name_ru="Медицина",
        icon="🏥",
        color="#EF4444",
        description_ru="Медицина: услуги, контент, ответы пациентам.",
    ),
    "real_estate": _skeleton(
        vid="real_estate",
        name_ru="Недвижимость",
        icon="🏠",
        color="#0EA5E9",
        description_ru="Недвижимость: объекты, реклама, презентации.",
    ),
    "education": _skeleton(
        vid="education",
        name_ru="Образование",
        icon="📚",
        color="#8B5CF6",
        description_ru="Образование: курсы, воронки, контент.",
    ),
    "marketplace": _skeleton(
        vid="marketplace",
        name_ru="Marketplace",
        icon="🛒",
        color="#EC4899",
        description_ru="Marketplace: карточки товаров, реклама.",
    ),
    "owner": _skeleton(
        vid="owner",
        name_ru="Owner AI",
        icon="👑",
        color="#111827",
        description_ru="Режим владельца: аналитика, КП, презентации, реклама.",
        scenarios=("Анализ продаж", "КП", "Презентация", "Прибыль", "Договор"),
    ),
}

FRAMEWORK_VERTICAL_IDS: tuple[str, ...] = tuple(VERTICAL_CONFIGS.keys())
