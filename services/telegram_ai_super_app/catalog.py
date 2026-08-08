"""Sprint 43.0 — Russian-first Telegram Super App catalogs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MenuButton:
    id: str
    label: str


@dataclass(frozen=True)
class StudioOption:
    id: str
    label: str
    modality: Literal["image", "video", "voice", "text", "prompt", "workflow", "document", "presentation", "ads"] | None
    vertical: str | None = None


# Canonical main-menu button texts (exact match for handlers).
class BTN:
    CONCIERGE = "🤖 AI Консьерж"
    DASHBOARD = "📊 Дашборд"
    TASKS = "📋 Задачи"
    NOTIFICATIONS = "🔔 Уведомления"
    BUSINESS = "🏢 Бизнес"
    AI_STUDIO = "🎨 Студия AI"
    SETTINGS = "⚙ Настройки"
    ALL_SECTIONS = "📂 Все разделы"
    DEVELOPER = "🧪 Лаборатория"
    DEV_WIP = "🚧 Разработка"
    HERCULES = "🟢 Hercules"
    AI_COMMAND = "🧠 AI Command"
    WORK_MODE = "⚙ Режим работы"
    MEMORY = "🧠 Память"
    AUTOMATION = "⚡ Автоматизация"
    BACK_MAIN = "⬅ Главное меню"
    BACK_STUDIO = "⬅ Студия AI"
    HISTORY = "📚 История"
    QUEUE = "⏳ Очередь"
    FAVORITES = "⭐ Избранное"
    BEAUTY = "💅 Beauty AI"
    ASK_AI = "💬 Спросить AI"
    TEMPLATES = "📦 Шаблоны"
    GENERATE_NOW = "✅ Сгенерировать"
    RUN_CHAIN = "▶ Запустить цепочку"


MAIN_MENU_BUTTONS: tuple[MenuButton, ...] = (
    MenuButton("concierge", BTN.CONCIERGE),
    MenuButton("ai_command", BTN.AI_COMMAND),
    MenuButton("work_mode", BTN.WORK_MODE),
    MenuButton("memory", BTN.MEMORY),
    MenuButton("automation", BTN.AUTOMATION),
    MenuButton("dashboard", BTN.DASHBOARD),
    MenuButton("tasks", BTN.TASKS),
    MenuButton("notifications", BTN.NOTIFICATIONS),
    MenuButton("business", BTN.BUSINESS),
    MenuButton("ai_studio", BTN.AI_STUDIO),
    MenuButton("settings", BTN.SETTINGS),
    MenuButton("all_sections", BTN.ALL_SECTIONS),
)

DEVELOPER_MENU_BUTTONS: tuple[MenuButton, ...] = (
    MenuButton("hercules", BTN.HERCULES),
    MenuButton("platform_builder", "Конструктор платформы"),
    MenuButton("runtime", "Среда выполнения"),
    MenuButton("context_engine", "Движок контекста"),
    MenuButton("event_bus", "Шина событий"),
    MenuButton("project_memory", "Память проектов"),
    MenuButton("skills", "Навыки AI"),
    MenuButton("voice_runtime", "Голосовая среда"),
    MenuButton("control_tower", "Диспетчерская"),
    MenuButton("service_builder", "Конструктор сервисов"),
    MenuButton("health", "Здоровье платформы"),
    MenuButton("security", "Безопасность"),
    MenuButton("developer_console", "Консоль разработчика"),
)

# Developer menu — fully Russian labels.
DEVELOPER_MENU_LABELS_RU: dict[str, str] = {
    "platform_builder": "Конструктор платформы",
    "runtime": "Среда выполнения",
    "context_engine": "Движок контекста",
    "event_bus": "Шина событий",
    "project_memory": "Память проектов",
    "skills": "Навыки AI",
    "voice_runtime": "Голосовая среда",
    "control_tower": "Диспетчерская",
    "integrations": "Интеграции",
    "security": "Безопасность",
    "health": "Здоровье платформы",
    "service_builder": "Конструктор сервисов",
    "developer_console": "Консоль разработчика",
}

# Sprint 43.3 — task-oriented AI Studio menu (no tech jargon)
AI_STUDIO_OPTIONS: tuple[StudioOption, ...] = (
    StudioOption("image", "🎨 Создать изображение", "image"),
    StudioOption("video", "🎥 Создать видео", "video"),
    StudioOption("voice", "🎙 Озвучить текст", "voice"),
    StudioOption("voice_clone", "🎤 Клонировать голос", "voice"),
    StudioOption("reels", "📱 Создать Reels", "video"),
    StudioOption("ads", "📢 Создать рекламу", "ads"),
    StudioOption("document", "📄 Создать документ", "document"),
    StudioOption("presentation", "📊 Создать презентацию", "presentation"),
    StudioOption("text", "📝 Написать текст", "text"),
    StudioOption("prompt", "💡 Улучшить промпт", "prompt"),
    StudioOption("history", "📚 История", None),
    StudioOption("favorites", "⭐ Избранное", None),
    StudioOption("settings", "⚙ Настройки", None),
    StudioOption("beauty", "💅 Beauty AI", "workflow", vertical="beauty"),
    StudioOption("templates", "📦 Шаблоны", None),
)

CONCIERGE_EXAMPLES: tuple[str, ...] = (
    "Создай рекламу",
    "Создай видео",
    "Создай картинку",
    "Озвучь текст",
    "Открыть студию AI",
    "Проанализируй продажи",
    "Подготовь КП",
    "Создай договор",
    "Покажи прибыль",
    "Создай презентацию",
)

BUSINESS_SECTIONS: tuple[MenuButton, ...] = (
    MenuButton("crm", "📇 CRM"),
    MenuButton("auto", "🚗 Авто"),
    MenuButton("crypto", "💰 Crypto OTC"),
    MenuButton("drone", "🚁 Дроны"),
    MenuButton("agro", "🌾 Агро"),
    MenuButton("beauty", "💄 Красота"),
    MenuButton("legal", "⚖ Юриспруденция"),
    MenuButton("travel", "✈ Travel"),
)

ALL_SECTIONS: tuple[MenuButton, ...] = (
    MenuButton("history", BTN.HISTORY),
    MenuButton("queue", BTN.QUEUE),
    MenuButton("favorites", BTN.FAVORITES),
    MenuButton("documents", "📄 Документы"),
    MenuButton("analytics", "📈 Аналитика"),
    MenuButton("calendar", "📅 Календарь"),
    MenuButton("files", "📂 Файлы"),
    MenuButton("search", "🔎 Поиск"),
    MenuButton("developer", BTN.DEVELOPER),
)

IMAGE_SIZES = ("1024×1024", "1080×1080", "1080×1920", "1920×1080")
IMAGE_STYLES = ("Реализм", "Минимализм", "Премиум", "Яркий маркетинг", "Кино")
IMAGE_PLATFORMS = ("Instagram", "TikTok", "Facebook", "YouTube", "Telegram", "LinkedIn")
IMAGE_QUALITIES = ("Стандарт", "Высокое", "Максимум")

VIDEO_DURATIONS = ("15 сек", "30 сек", "60 сек", "2 мин")
VIDEO_FORMATS = ("Вертикальное 9:16", "Горизонтальное 16:9", "Квадрат 1:1")
VIDEO_STYLES = ("Рекламный", "Документальный", "Динамичный Reels", "Корпоративный")
VIDEO_FPS = ("24 FPS", "30 FPS", "60 FPS")

VOICE_MODES = (
    "Озвучка текста",
    "Клон голоса",
    "Коммерческий голос",
    "Диктор",
    "Подкаст",
    "Голос рекламы",
    "Голос Reels",
    "Голос презентации",
    "Голос AI",
)

PROMPT_CATEGORIES = (
    "Фото",
    "Видео",
    "Изображения",
    "Красота",
    "Маркетинг",
    "Продажи",
    "CRM",
    "ERP",
    "Юридические документы",
    "Дроны",
    "Crypto OTC",
    "Agro",
    "Auto",
)

FOLLOW_UP_ACTIONS = (
    "ещё 5 вариантов",
    "измени стиль",
    "сделай лучше",
    "сделай короче",
    "переведи",
    "создай видео из этого",
    "создай изображение из этого",
    "создай озвучку",
)

POST_GEN_WORKFLOW = (
    ("download", "📥 Скачать"),
    ("retry", "🔄 Повторить"),
    ("edit", "✏ Изменить"),
    ("fav", "❤️ В избранное"),
    ("video", "🎥 Видео"),
    ("voice", "🎤 Озвучка"),
    ("reels", "📱 Reels"),
    ("ads", "📢 Реклама"),
    ("send", "📤 Отправить"),
    ("export", "📄 Экспорт"),
    ("chain", "▶ Продолжить цепочку"),
)

# Keep Russian UI; product brands (OpenAI etc.) only in provider ids.
PUBLISH_CHANNELS_RU = (
    ("instagram", "Instagram"),
    ("facebook", "Facebook"),
    ("tiktok", "TikTok"),
    ("youtube", "YouTube"),
    ("telegram", "Telegram"),
    ("linkedin", "LinkedIn"),
)
