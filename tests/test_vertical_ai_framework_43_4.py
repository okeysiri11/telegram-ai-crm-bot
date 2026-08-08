"""Sprint 43.4 — Vertical AI Framework + Beauty AI reference vertical."""

from __future__ import annotations

import pytest

from platform_vertical_ai.agents import COPYWRITER_CHANNELS, DESIGNER_PRODUCTS, VIDEO_PRODUCTS, VOICE_PRODUCTS, agent_catalog
from platform_vertical_ai.configs.beauty import BEAUTY_CONFIG
from platform_vertical_ai.framework import VerticalAiFramework, VERSION
from platform_vertical_ai.models import VerticalConfig, VerticalMenuItem, VerticalAgent, WizardQuestion
from platform_vertical_ai.registry import vertical_registry
from platform_vertical_ai.wizard import build_vertical_prompt, calendar_plan, chain_plan
from services.telegram_ai_super_app.catalog import BTN
from services.telegram_ai_super_app.keyboards import ai_studio_keyboard
from services.telegram_ai_super_app.vertical_ux import vertical_menu_keyboard


class TestVerticalFramework:
    def test_version(self):
        assert VERSION == "43.4"
        assert VerticalAiFramework.VERSION == "43.4"

    def test_all_framework_verticals_registered(self):
        required = {
            "beauty",
            "auto",
            "construction",
            "legal",
            "crypto",
            "agro",
            "travel",
            "production",
            "manufacturing",
            "cafe",
            "medical",
            "real_estate",
            "education",
            "marketplace",
            "owner",
        }
        ids = set(vertical_registry.list_ids())
        assert required <= ids

    def test_beauty_is_complete_reference(self):
        complete = vertical_registry.complete_verticals()
        assert any(c.id == "beauty" for c in complete)
        assert BEAUTY_CONFIG.complete is True

    def test_new_vertical_by_config_only(self):
        fw = VerticalAiFramework()
        custom = VerticalConfig(
            id="demo_vert",
            name_ru="Демо",
            icon="✨",
            color="#000",
            description_ru="Тестовая вертикаль",
            menu=(VerticalMenuItem("ads", "📢 Реклама", "studio", modality="ads"),),
            agents=(VerticalAgent("copywriter", "Копирайтер", "copywriter"),),
            scenarios=("Тест",),
            wizard=(WizardQuestion("goal", "Цель?"),),
            prompt_library=(),
            complete=False,
        )
        fw.registry.register(custom)
        assert fw.get("demo_vert").name_ru == "Демо"
        assert "Название" in fw.new_vertical_checklist()

    def test_inherit_capabilities(self):
        for cap in ("ai_chat", "ai_studio", "crm", "telegram", "history", "favorites"):
            assert cap in BEAUTY_CONFIG.inherit


class TestBeautyVertical:
    def test_beauty_menu(self):
        labels = BEAUTY_CONFIG.menu_labels()
        for required in (
            "💅 Создать пост",
            "🎥 Создать Reels",
            "📸 До / После",
            "🎨 Баннер",
            "📢 Акция",
            "🎁 Сертификат",
            "💲 Прайс",
            "📅 Контент-план",
            "💬 Ответ клиенту",
            "📱 История",
            "⭐ Избранное",
            "⚙ Настройки",
        ):
            assert required in labels

    def test_beauty_scenarios(self):
        for s in ("Маникюр", "Косметология", "Барбер", "SPA", "До / После", "Видео процедуры"):
            assert s in BEAUTY_CONFIG.scenarios

    def test_beauty_wizard(self):
        ids = [q.id for q in BEAUTY_CONFIG.wizard]
        assert ids == ["business", "service", "goal", "audience", "platform"]

    def test_beauty_agents(self):
        roles = {a.role for a in BEAUTY_CONFIG.agents}
        assert {"copywriter", "designer", "video", "voice", "marketing"} <= roles
        catalog = agent_catalog(BEAUTY_CONFIG)
        assert "Instagram" in catalog["copywriter"]
        assert "Баннер" in DESIGNER_PRODUCTS
        assert "Reels" in VIDEO_PRODUCTS
        assert "Женский голос" in VOICE_PRODUCTS
        assert len(COPYWRITER_CHANNELS) >= 8

    def test_prompt_library_categories(self):
        cats = {p.category for p in BEAUTY_CONFIG.prompt_library}
        assert "Instagram" in cats
        assert "Telegram" in cats
        assert "Дизайн" in cats

    def test_calendar_and_marketing(self):
        fw = VerticalAiFramework()
        text = fw.calendar_text("beauty", 30)
        assert "Контент-план" in text
        assert "День 1" in text
        m = fw.marketing_text("beauty")
        assert "лояльности" in m.lower() or "Лояльности" in m or "Акция" in m

    def test_chain_plan(self):
        answers = {
            "business": "Салон красоты",
            "service": "Маникюр",
            "goal": "Привлечь клиентов",
            "audience": "Женщины 25–45",
            "platform": "Instagram",
        }
        prompt = build_vertical_prompt(BEAUTY_CONFIG, answers, intent="Пост")
        assert "Маникюр" in prompt
        steps = chain_plan(BEAUTY_CONFIG, answers)
        assert any(s["id"] == "image" for s in steps)
        assert any(s["id"] == "publish_ready" for s in steps)
        plan = calendar_plan(BEAUTY_CONFIG, 7)
        assert len(plan) == 7


class TestBeautyTelegram:
    def test_beauty_entry_label(self):
        assert BTN.BEAUTY == "💅 Beauty AI"
        kb = ai_studio_keyboard()
        flat = [b.text for row in kb.keyboard for b in row]
        assert "💅 Beauty AI" in flat

    def test_vertical_menu_keyboard(self):
        kb = vertical_menu_keyboard("beauty")
        flat = [b.text for row in kb.keyboard for b in row]
        assert "💅 Создать пост" in flat
        assert "🎥 Создать Reels" in flat
        assert BTN.ASK_AI in flat

    @pytest.mark.asyncio
    async def test_beauty_generation(self):
        from platform_ai.pipeline import UnifiedAiPipeline

        pipe = UnifiedAiPipeline()
        fw = VerticalAiFramework(pipeline=pipe)
        task = await fw.run_menu_generation(
            "tg:beauty",
            "beauty",
            menu_id="post",
            answers={
                "business": "Салон",
                "service": "Маникюр",
                "goal": "Акция",
                "audience": "Женщины",
                "platform": "Instagram",
            },
        )
        assert task.status == "готово"
        assert task.vertical == "beauty"
        hist = fw.history_text("tg:beauty", "beauty")
        assert "История" in hist


class TestLocalizationAndSmoke:
    def test_russian_menu(self):
        for m in BEAUTY_CONFIG.menu:
            assert any("а" <= c.lower() <= "я" or c in "ёЁ" for c in m.label) or any(
                x in m.label for x in ("Reels", "AI", "SPA")
            )

    def test_router_imports(self):
        from routers.telegram_super_app_router import router, vfw

        assert router.name == "telegram_super_app"
        assert vfw.get("beauty").complete

    def test_service_version(self):
        from services.telegram_ai_super_app.service import TelegramAiSuperApp

        assert TelegramAiSuperApp.VERSION == "43.4"
