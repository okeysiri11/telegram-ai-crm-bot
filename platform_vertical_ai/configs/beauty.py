"""Beauty AI — first complete vertical (Sprint 43.4 reference)."""

from __future__ import annotations

from platform_vertical_ai.models import (
    CrmEntity,
    DocumentType,
    KnowledgeTopic,
    PromptEntry,
    VerticalAgent,
    VerticalConfig,
    VerticalMenuItem,
    WizardQuestion,
)

BEAUTY_MENU: tuple[VerticalMenuItem, ...] = (
    VerticalMenuItem("post", "💅 Создать пост", "studio", modality="ads", agent="copywriter"),
    VerticalMenuItem("reels", "🎥 Создать Reels", "studio", modality="video", agent="video"),
    VerticalMenuItem("before_after", "📸 До / После", "studio", modality="image", agent="designer"),
    VerticalMenuItem("banner", "🎨 Баннер", "studio", modality="image", agent="designer"),
    VerticalMenuItem("promo", "📢 Акция", "studio", modality="ads", agent="marketing"),
    VerticalMenuItem("certificate", "🎁 Сертификат", "studio", modality="image", agent="designer"),
    VerticalMenuItem("price", "💲 Прайс", "studio", modality="document", agent="designer"),
    VerticalMenuItem("calendar", "📅 Контент-план", "calendar", agent="marketing"),
    VerticalMenuItem("reply", "💬 Ответ клиенту", "studio", modality="text", agent="copywriter"),
    VerticalMenuItem("history", "📱 История", "history"),
    VerticalMenuItem("favorites", "⭐ Избранное", "favorites"),
    VerticalMenuItem("settings", "⚙ Настройки", "settings"),
)

BEAUTY_AGENTS: tuple[VerticalAgent, ...] = (
    VerticalAgent(
        "copywriter",
        "AI Копирайтер",
        "copywriter",
        ("instagram", "telegram", "tiktok", "facebook", "google_business", "service_desc", "client_reply", "seo"),
        "text",
    ),
    VerticalAgent(
        "designer",
        "AI Дизайнер",
        "designer",
        ("banner", "poster", "story", "reels_cover", "menu", "price", "certificate", "card"),
        "image",
    ),
    VerticalAgent(
        "video",
        "AI Видео",
        "video",
        ("reels", "tiktok", "shorts", "ads", "procedure", "promo_video"),
        "video",
    ),
    VerticalAgent(
        "voice",
        "AI Голос",
        "voice",
        ("tts", "female", "male", "premium", "clone"),
        "voice",
    ),
    VerticalAgent(
        "marketing",
        "AI Маркетинг",
        "marketing",
        ("promo", "discount", "upsell", "loyalty", "repeat"),
        "ads",
    ),
)

BEAUTY_SCENARIOS: tuple[str, ...] = (
    "Маникюр",
    "Косметология",
    "Парикмахер",
    "Барбер",
    "SPA",
    "Массаж",
    "Перманентный макияж",
    "Лазер",
    "Подарочный сертификат",
    "Акция",
    "До / После",
    "Новинка",
    "Видео процедуры",
)

BEAUTY_WIZARD: tuple[WizardQuestion, ...] = (
    WizardQuestion(
        "business",
        "Какой бизнес?",
        ("Салон красоты", "Ногтевая студия", "Барбершоп", "SPA", "Косметология", "Другое"),
    ),
    WizardQuestion(
        "service",
        "Какая услуга?",
        BEAUTY_SCENARIOS,
    ),
    WizardQuestion(
        "goal",
        "Какая цель?",
        ("Привлечь клиентов", "Акция", "Новинка", "До / После", "Повторные продажи"),
    ),
    WizardQuestion(
        "audience",
        "Какая аудитория?",
        ("Женщины 25–45", "Мужчины", "Премиум", "Молодёжь", "Семьи"),
    ),
    WizardQuestion(
        "platform",
        "Где публикуем?",
        ("Instagram", "Telegram", "TikTok", "Facebook", "Google Business"),
    ),
)

BEAUTY_PROMPTS: tuple[PromptEntry, ...] = (
    PromptEntry("b_ig_post", "Instagram", "Пост услуги", "Instagram-пост салона красоты, премиум, русский"),
    PromptEntry("b_ig_story", "Instagram", "Сторис акции", "Instagram Story с акцией месяца"),
    PromptEntry("b_tg", "Telegram", "Пост в Telegram", "Тёплый пост для Telegram-канала салона"),
    PromptEntry("b_tt", "TikTok", "Сценарий TikTok", "Короткий TikTok сценарий процедуры"),
    PromptEntry("b_fb", "Facebook", "Реклама Facebook", "Рекламный текст Facebook для салона"),
    PromptEntry("b_gmb", "Google Business", "Google Business", "Описание для Google Business Profile"),
    PromptEntry("b_svc", "Услуги", "Описание услуги", "Продающее описание beauty-услуги"),
    PromptEntry("b_reply", "Клиенты", "Ответ клиенту", "Вежливый ответ клиенту в Direct / Telegram"),
    PromptEntry("b_seo", "SEO", "SEO-текст", "SEO-описание салона красоты"),
    PromptEntry("b_banner", "Дизайн", "Баннер", "Баннер акции салона красоты"),
    PromptEntry("b_cert", "Дизайн", "Сертификат", "Подарочный сертификат салона"),
    PromptEntry("b_price", "Дизайн", "Прайс", "Элегантный прайс-лист услуг"),
    PromptEntry("b_reels", "Видео", "Reels", "Reels до/после процедуры"),
    PromptEntry("b_voice", "Голос", "Озвучка акции", "Женский премиум-голос для рекламы салона"),
)

BEAUTY_CONFIG = VerticalConfig(
    id="beauty",
    name_ru="Beauty AI",
    icon="💅",
    color="#E8A0BF",
    description_ru=(
        "Первая полноценная вертикаль ADOS: контент, реклама, Reels, озвучка, "
        "календарь и ответы клиентам для салонов красоты."
    ),
    menu=BEAUTY_MENU,
    agents=BEAUTY_AGENTS,
    scenarios=BEAUTY_SCENARIOS,
    wizard=BEAUTY_WIZARD,
    prompt_library=BEAUTY_PROMPTS,
    crm_entities=(
        CrmEntity("client", "Клиент"),
        CrmEntity("appointment", "Запись"),
        CrmEntity("service", "Услуга"),
        CrmEntity("loyalty", "Лояльность"),
    ),
    document_types=(
        DocumentType("price_list", "Прайс"),
        DocumentType("certificate", "Сертификат"),
        DocumentType("consent", "Согласие на процедуру"),
        DocumentType("promo", "Акция"),
    ),
    knowledge=(
        KnowledgeTopic("manicure", "Маникюр", "Уход за ногтями, дизайн, гигиена"),
        KnowledgeTopic("cosmo", "Косметология", "Уход за лицом, аппаратные процедуры"),
        KnowledgeTopic("hair", "Парикмахер", "Стрижки, окрашивание, укладки"),
        KnowledgeTopic("spa", "SPA", "Релакс, массаж, комплексный уход"),
    ),
    calendar_periods=(7, 14, 30, 90),
    marketing_offers=(
        "Акция месяца",
        "Скидка на комплекс услуг",
        "Повышение среднего чека (upsell)",
        "Программа лояльности",
        "Повторные продажи через напоминания",
        "Подарочный сертификат как лид-магнит",
    ),
    dashboard_widgets=("history", "favorites", "calendar", "marketing", "agents"),
    complete=True,
    enabled=True,
)
