"""Shared stubs — skeleton VerticalConfig for industries not yet fully productized."""

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


def _skeleton(
    *,
    vid: str,
    name_ru: str,
    icon: str,
    color: str,
    description_ru: str,
    scenarios: tuple[str, ...] | None = None,
) -> VerticalConfig:
    """Minimal config — enough for Framework Ready (no code copy to add a vertical)."""
    return VerticalConfig(
        id=vid,
        name_ru=name_ru,
        icon=icon,
        color=color,
        description_ru=description_ru,
        menu=(
            VerticalMenuItem("chat", "💬 Спросить AI", "wizard"),
            VerticalMenuItem("ads", "📢 Создать рекламу", "studio", modality="ads"),
            VerticalMenuItem("image", "🎨 Создать изображение", "studio", modality="image"),
            VerticalMenuItem("video", "🎥 Создать видео", "studio", modality="video"),
            VerticalMenuItem("voice", "🎙 Озвучить", "studio", modality="voice"),
            VerticalMenuItem("doc", "📄 Документ", "studio", modality="document"),
            VerticalMenuItem("calendar", "📅 Контент-план", "calendar"),
            VerticalMenuItem("history", "📱 История", "history"),
            VerticalMenuItem("favorites", "⭐ Избранное", "favorites"),
            VerticalMenuItem("settings", "⚙ Настройки", "settings"),
        ),
        agents=(
            VerticalAgent("copywriter", "AI Копирайтер", "copywriter", ("instagram", "telegram", "seo")),
            VerticalAgent("designer", "AI Дизайнер", "designer", ("banner", "story"), "image"),
            VerticalAgent("video", "AI Видео", "video", ("reels", "ads"), "video"),
            VerticalAgent("voice", "AI Голос", "voice", ("tts", "clone"), "voice"),
            VerticalAgent("marketing", "AI Маркетинг", "marketing", ("promo", "loyalty")),
        ),
        scenarios=scenarios
        or (
            "Реклама",
            "Пост",
            "Видео",
            "Акция",
            "КП",
        ),
        wizard=(
            WizardQuestion("business", "Какой бизнес?", None),
            WizardQuestion("goal", "Какая цель?", ("Продажи", "Охват", "Заявки", "Бренд")),
            WizardQuestion("audience", "Какая аудитория?", None),
            WizardQuestion("platform", "Где публикуем?", ("Instagram", "Telegram", "TikTok", "Сайт")),
        ),
        prompt_library=(
            PromptEntry(f"{vid}_ads", "Реклама", "Базовая реклама", f"Реклама для {name_ru}"),
            PromptEntry(f"{vid}_post", "Посты", "Пост", f"Пост для {name_ru}"),
        ),
        crm_entities=(CrmEntity("lead", "Лид"), CrmEntity("client", "Клиент"), CrmEntity("deal", "Сделка")),
        document_types=(DocumentType("kp", "КП"), DocumentType("contract", "Договор")),
        knowledge=(KnowledgeTopic(f"{vid}_intro", name_ru, description_ru),),
        marketing_offers=("Акция недели", "Скидка постоянным", "Комплекс услуг"),
        complete=False,
    )
