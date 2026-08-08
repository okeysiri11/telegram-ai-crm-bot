"""Sprint 43.0 — Telegram AI Super App tests."""

from __future__ import annotations

import pytest

from keyboards import owner_main_menu, _owner_main_menu_legacy
from services.telegram_ai_super_app.catalog import (
    AI_STUDIO_OPTIONS,
    BTN,
    CONCIERGE_EXAMPLES,
    MAIN_MENU_BUTTONS,
    PROMPT_CATEGORIES,
)
from services.telegram_ai_super_app.concierge import plan_from_text, vertical_playbook
from services.telegram_ai_super_app.conversation import ConversationMemory
from services.telegram_ai_super_app.job_queue import JobQueue
from services.telegram_ai_super_app.keyboards import (
    ai_studio_keyboard,
    main_menu_keyboard,
    developer_menu_keyboard,
)
from services.telegram_ai_super_app.providers import (
    IMAGE_PROVIDERS,
    VIDEO_PROVIDERS,
    VOICE_PROVIDERS,
    SuperAppProviderFacade,
)
from services.telegram_ai_super_app.service import TelegramAiSuperApp
from services.telegram_ai_super_app.studios import compose_generation_prompt, studio_steps


def has_cyrillic(s: str) -> bool:
    return any("а" <= c.lower() <= "я" or c in "ёЁ" for c in s)


class TestMainMenu:
    def test_main_menu_buttons_exact(self):
        labels = [b.label for b in MAIN_MENU_BUTTONS]
        assert labels == [
            BTN.CONCIERGE,
            BTN.AI_COMMAND,
            BTN.WORK_MODE,
            BTN.MEMORY,
            BTN.AUTOMATION,
            BTN.DASHBOARD,
            BTN.TASKS,
            BTN.NOTIFICATIONS,
            BTN.BUSINESS,
            BTN.AI_STUDIO,
            BTN.SETTINGS,
            BTN.ALL_SECTIONS,
        ]

    def test_owner_main_menu_is_super_app_shell(self):
        kb = owner_main_menu()
        flat = [btn.text for row in kb.keyboard for btn in row]
        assert BTN.CONCIERGE in flat
        assert BTN.AI_STUDIO in flat
        assert "Platform Builder" not in flat
        assert "Context Engine" not in flat
        assert "Event Bus" not in flat
        assert "System Health" not in flat

    def test_legacy_fallback_also_simple(self):
        kb = _owner_main_menu_legacy()
        flat = [btn.text for row in kb.keyboard for btn in row]
        assert BTN.CONCIERGE in flat
        assert len(flat) >= 8

    def test_developer_menu_gated_labels_ru(self):
        kb = developer_menu_keyboard()
        flat = [btn.text for row in kb.keyboard for btn in row]
        assert any(has_cyrillic(t) for t in flat)
        assert BTN.BACK_MAIN in flat


class TestLocalization:
    def test_main_and_studio_labels_russian(self):
        for b in MAIN_MENU_BUTTONS:
            assert has_cyrillic(b.label) or "AI" in b.label
        for o in AI_STUDIO_OPTIONS:
            assert has_cyrillic(o.label) or "AI" in o.label or "Reels" in o.label or "Studio" in o.label

    def test_concierge_examples_russian(self):
        for ex in CONCIERGE_EXAMPLES:
            assert has_cyrillic(ex)


class TestConcierge:
    def test_routes_image(self):
        plan = plan_from_text("Создай картинку для Instagram")
        assert plan.modality == "image"
        assert plan.studio_id == "image"
        assert has_cyrillic(plan.reply_ru)

    def test_routes_video_voice_legal_auto(self):
        assert plan_from_text("сделай видео").studio_id == "video"
        assert plan_from_text("озвучь текст").studio_id == "voice"
        assert plan_from_text("создай договор").vertical == "legal"
        assert plan_from_text("объявление на AutoRia").vertical == "auto"

    def test_follow_up_remembers_modality(self):
        plan = plan_from_text("ещё 5 вариантов", last_modality="image")
        assert plan.intent == "follow_up"
        assert plan.modality == "image"

    def test_vertical_playbooks(self):
        for v in ("beauty", "auto", "crypto", "agro", "legal"):
            book = vertical_playbook(v)
            assert book["items"]
            assert has_cyrillic(book["title"]) or "AI" in book["title"]


class TestStudios:
    def test_image_steps(self):
        steps = studio_steps("image")
        assert steps[0]["id"] == "what"
        assert any(s["id"] == "size" for s in steps)
        assert any(s["id"] == "quality" for s in steps)

    def test_video_voice_prompt_steps(self):
        assert len(studio_steps("video")) >= 4
        assert studio_steps("voice")[0]["id"] == "mode"
        assert studio_steps("prompt")[0]["choices"] == list(PROMPT_CATEGORIES)

    def test_compose_prompt(self):
        p = compose_generation_prompt(
            "image",
            {
                "what": "баннер",
                "size": "1080×1080",
                "style": "Минимализм",
                "platform": "Instagram",
                "quality": "Высокое",
                "count": "3",
            },
        )
        assert "баннер" in p
        assert "Instagram" in p

    def test_ai_studio_keyboard_has_options(self):
        kb = ai_studio_keyboard()
        flat = [btn.text for row in kb.keyboard for btn in row]
        assert "🎨 Создать изображение" in flat
        assert "🎥 Создать видео" in flat
        assert "🎙 Озвучить текст" in flat
        assert "💡 Улучшить промпт" in flat
        assert "💅 Beauty AI" in flat
        assert BTN.ASK_AI in flat


class TestMemoryAndQueue:
    def test_conversation_memory(self):
        mem = ConversationMemory(max_turns=10)
        key = mem.key(42)
        mem.add(key, "user", "создай картинку")
        mem.add(key, "ai", "ок")
        mem.set_context(key, last_modality="image")
        assert mem.last_ai(key).text == "ок"
        assert mem.get_context(key)["last_modality"] == "image"

    def test_job_queue_lifecycle(self):
        q = JobQueue()
        job = q.create("u1", "image", "тест")
        assert job.status in ("создана", "в_очереди", "ожидает")
        q.mark_running(job.id, provider_id="openai_image")
        q.mark_progress(job.id, 50)
        done = q.mark_done(job.id, {"provider_id": "openai_image", "content": "img"})
        assert done.status == "готово"
        assert done.progress == 100
        assert "openai_image" in done.status_line_ru()


class TestProviders:
    def test_provider_lists_no_telegram_binding(self):
        assert "openai_image" in IMAGE_PROVIDERS
        assert "google_imagen" in IMAGE_PROVIDERS
        assert "flux_image" in IMAGE_PROVIDERS
        assert "google_veo" in VIDEO_PROVIDERS
        assert "runway_video" in VIDEO_PROVIDERS
        assert "elevenlabs_voice" in VOICE_PROVIDERS
        assert "azure_speech" in VOICE_PROVIDERS

    @pytest.mark.asyncio
    async def test_generate_via_provider_layer(self):
        facade = SuperAppProviderFacade()
        result = await facade.generate("image", "тест баннер", preferred="openai_image")
        assert result["via"] == "provider_layer"
        assert result["provider_id"]
        assert result["modality"] == "image"

    def test_prepare_publish(self):
        facade = SuperAppProviderFacade()
        job = facade.prepare_publish(
            channel="instagram",
            asset_ref="media://x",
            caption="привет",
        )
        assert job["status"] == "prepared"
        assert job["provider_id"] == "instagram_publish"


class TestService:
    @pytest.mark.asyncio
    async def test_run_generation_and_history(self):
        svc = TelegramAiSuperApp()
        key = svc.user_key(99)
        job = await svc.run_generation(
            key,
            studio_id="image",
            answers={"what": "логотип", "size": "1024×1024", "style": "Реализм", "platform": "Telegram", "count": "1", "quality": "Стандарт"},
        )
        assert job.status == "готово"
        hist = svc.history_text(key)
        assert "История" in hist or "история" in hist.lower() or "#" in hist

    def test_concierge_message_persists(self):
        svc = TelegramAiSuperApp()
        key = svc.user_key(1001)
        out = svc.handle_concierge_message(key, "Проверить CRM")
        assert out["plan"].vertical == "crm"
        assert svc.memory.history(key)
        follow = svc.handle_concierge_message(key, "сделай короче")
        assert follow["plan"].intent == "follow_up"


class TestRouterImport:
    def test_router_imports(self):
        from routers.telegram_super_app_router import router

        assert router.name == "telegram_super_app"

    def test_startup_lists_add_vehicle_before_super_app(self):
        from startup import BOT_ROUTER_PATHS

        assert BOT_ROUTER_PATHS[0] == "routers.auto_add_vehicle_router"
        assert BOT_ROUTER_PATHS[1] == "routers.telegram_super_app_router"


def test_main_menu_keyboard_structure():
    kb = main_menu_keyboard(include_developer=True)
    flat = [btn.text for row in kb.keyboard for btn in row]
    assert BTN.DEVELOPER in flat
    assert BTN.ASK_AI in flat
    assert BTN.AI_STUDIO == "🎨 Студия AI"
