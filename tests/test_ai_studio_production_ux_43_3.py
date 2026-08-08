"""Sprint 43.3 — AI Studio Production UX + Conversational AI + Beauty templates."""

from __future__ import annotations

import pytest

from services.telegram_ai_super_app.catalog import AI_STUDIO_OPTIONS, BTN, POST_GEN_WORKFLOW
from services.telegram_ai_super_app.conversation_flow import (
    ConversationDraft,
    build_prompt_from_draft,
    detect_studio_from_text,
    is_short_idea,
    steps_for,
)
from services.telegram_ai_super_app.keyboards import (
    ai_studio_keyboard,
    main_menu_keyboard,
    post_generation_inline,
)
from services.telegram_ai_super_app.product_ux import (
    format_result_for_user,
    progress_message,
    sanitize_user_text,
)
from services.telegram_ai_super_app.service import TelegramAiSuperApp
from services.telegram_ai_super_app.studios import BEAUTY_SCENARIOS
from services.telegram_ai_super_app.templates import TEMPLATE_CATEGORIES, TEMPLATES, templates_by_category


def has_cyrillic(s: str) -> bool:
    return any("а" <= c.lower() <= "я" or c in "ёЁ" for c in s)


class TestLocalization43_3:
    def test_studio_task_menu_russian(self):
        labels = {o.label for o in AI_STUDIO_OPTIONS}
        assert "🎨 Создать изображение" in labels
        assert "🎥 Создать видео" in labels
        assert "🎙 Озвучить текст" in labels
        assert "🎤 Клонировать голос" in labels
        assert "📱 Создать Reels" in labels
        assert "📢 Создать рекламу" in labels
        assert "📄 Создать документ" in labels
        assert "📊 Создать презентацию" in labels
        assert "📝 Написать текст" in labels
        assert "💡 Улучшить промпт" in labels
        assert "📚 История" in labels
        assert "⭐ Избранное" in labels
        assert BTN.AI_STUDIO == "🎨 Студия AI"
        assert BTN.ASK_AI == "💬 Спросить AI"

    def test_no_english_tech_in_studio_labels(self):
        banned = ("Provider", "Pipeline", "Runtime", "Vault", "Flux", "Replicate", "Runway", "Veo")
        for o in AI_STUDIO_OPTIONS:
            for b in banned:
                assert b not in o.label

    def test_welcome_copy_sanitized(self):
        svc = TelegramAiSuperApp()
        for text in (
            svc.welcome_studio(),
            svc.welcome_concierge(),
            svc.welcome_settings(),
            svc.owner_dashboard_text("u"),
        ):
            assert "Provider" not in text
            assert "Pipeline" not in text
            assert "Runtime" not in text
            assert has_cyrillic(text)


class TestConversation43_3:
    def test_short_idea_detected(self):
        assert is_short_idea("Хочу рекламу")
        assert is_short_idea("Создай видео")
        assert not is_short_idea("Создай рекламу салона красоты для женщин 25–45 в стиле премиум")

    def test_detect_studio(self):
        assert detect_studio_from_text("Хочу рекламу") == "ads"
        assert detect_studio_from_text("сделай reels") == "reels"
        assert detect_studio_from_text("озвучь текст") == "voice"
        assert detect_studio_from_text("клонируй голос") == "voice_clone"

    def test_clarify_max_three_steps(self):
        for sid in ("ads", "image", "video", "reels", "voice", "text", "prompt"):
            assert len(steps_for(sid)) <= 3

    def test_build_prompt_from_draft(self):
        draft = ConversationDraft(
            intent="ads",
            studio_id="ads",
            answers={"business": "Салон красоты", "audience": "Женщины 25–45", "goal": "Привлечь клиентов"},
        )
        prompt = build_prompt_from_draft(draft)
        assert "Салон красоты" in prompt
        assert "русский" in prompt.lower() or "Русский" in prompt

    def test_concierge_clarify_path(self):
        svc = TelegramAiSuperApp()
        out = svc.handle_concierge_message("u:clarify", "Хочу рекламу")
        assert out["needs_clarify"] is True
        assert out["studio_id"] == "ads"
        assert "Provider" not in out["text"]


class TestBeautyAndTemplates43_3:
    def test_beauty_scenarios(self):
        required = (
            "Instagram Post",
            "Instagram Story",
            "Reels",
            "TikTok",
            "Видео акции",
            "Прайс",
            "Подарочный сертификат",
            "Баннер",
            "До / После",
            "Акция месяца",
            "Описание услуги",
            "Контент-план",
            "Ответ клиенту",
            "Ответ в Direct",
            "Ответ в Telegram",
            "Маркетинговый календарь",
        )
        for r in required:
            assert r in BEAUTY_SCENARIOS

    def test_template_categories(self):
        assert "Красота" in TEMPLATE_CATEGORIES
        assert "Автобизнес" in TEMPLATE_CATEGORIES
        assert "Производство" in TEMPLATE_CATEGORIES
        assert len(TEMPLATE_CATEGORIES) == 10
        assert templates_by_category("Красота")
        assert len(TEMPLATES) >= 10


class TestProductUx43_3:
    def test_sanitize_tech_leaks(self):
        raw = "AI Runtime → Provider Manager sandbox Flux Runway Veo"
        cleaned = sanitize_user_text(raw)
        assert "Provider Manager" not in cleaned
        assert "Flux" not in cleaned or "система" in cleaned

    def test_progress_steps_ru(self):
        assert "Подготовка" in progress_message("prepare")
        assert "очереди" in progress_message("queue").lower() or "Очереди" in progress_message("queue")
        assert "Генерация" in progress_message("generate")
        assert "Обработка" in progress_message("process")
        assert "Готово" in progress_message("done")
        assert "сек" in progress_message("generate", eta_sec=12)

    def test_post_gen_buttons(self):
        labels = [lab for _, lab in POST_GEN_WORKFLOW]
        assert "📥 Скачать" in labels
        assert "🔄 Повторить" in labels
        assert "❤️ В избранное" in labels
        assert "🎥 Видео" in labels
        assert "🎤 Озвучка" in labels
        assert "📱 Reels" in labels
        assert "📢 Реклама" in labels

    def test_ask_ai_on_main_and_studio(self):
        main = [b.text for row in main_menu_keyboard().keyboard for b in row]
        studio = [b.text for row in ai_studio_keyboard().keyboard for b in row]
        assert BTN.ASK_AI in main
        assert BTN.ASK_AI in studio


class TestHistoryFavorites43_3:
    @pytest.mark.asyncio
    async def test_history_and_favorites(self):
        from platform_ai.pipeline import UnifiedAiPipeline

        pipe = UnifiedAiPipeline()
        svc = TelegramAiSuperApp(pipeline=pipe)
        key = "tg:43.3"
        task = await svc.run_generation(
            key,
            studio_id="ads",
            answers={"what": "реклама салона", "business": "Салон", "goal": "Клиенты"},
        )
        hist = svc.history_text(key)
        assert "История" in hist
        assert "Provider" not in hist
        pipe.toggle_favorite(task.id)
        fav = svc.favorites_text(key)
        assert "Избранное" in fav
        body = format_result_for_user(task)
        assert "Готово" in body
        assert "sandbox" not in body.lower() or "черновик" in body.lower()


class TestOwnerAi43_3:
    def test_owner_hints(self):
        svc = TelegramAiSuperApp()
        assert svc.owner_ai_reply("Проанализируй продажи")
        assert svc.owner_ai_reply("Подготовь КП")
        assert svc.owner_ai_reply("Покажи прибыль")
        assert "договор" in (svc.owner_ai_reply("Напиши договор") or "").lower() or svc.owner_ai_reply("Напиши договор")


class TestServiceVersion43_3:
    def test_version(self):
        assert TelegramAiSuperApp.VERSION in ("43.3", "43.4")

    def test_studio_steps_short(self):
        svc = TelegramAiSuperApp()
        assert len(svc.studio_steps("ads")) <= 3
        assert len(svc.studio_steps("image")) <= 3

    def test_post_generation_inline_builds(self):
        kb = post_generation_inline("job-1")
        flat = [b.text for row in kb.inline_keyboard for b in row]
        assert "📥 Скачать" in flat
        assert "❤️ В избранное" in flat


class TestRouterSmoke43_3:
    def test_router_imports(self):
        from routers.telegram_super_app_router import router

        assert router.name == "telegram_super_app"

    def test_no_provider_jargon_in_router_source(self):
        from pathlib import Path

        src = Path("routers/telegram_super_app_router.py").read_text(encoding="utf-8")
        # User-facing string literals must not leak tech (allow comments/imports of modules)
        for bad in ('"Provider Layer', '"AI Runtime', "sandbox')", "Provider Manager…"):
            assert bad not in src
