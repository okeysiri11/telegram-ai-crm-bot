"""Sprint 43.1 — Unified AI Runtime Pipeline tests."""

from __future__ import annotations

import pytest

from platform_ai.pipeline import UnifiedAiPipeline, unified_ai_pipeline, PROVIDER_CATALOG
from platform_ai.pipeline_models import AiTaskRequest, AiTaskStatus, BEAUTY_STUDIO_PRODUCTS
from platform_ai.prompt_engine import PromptEngine
from services.telegram_ai_super_app.catalog import AI_STUDIO_OPTIONS, BTN, MAIN_MENU_BUTTONS
from services.telegram_ai_super_app.keyboards import ai_studio_keyboard, developer_menu_keyboard
from services.telegram_ai_super_app.service import TelegramAiSuperApp
from services.telegram_ai_super_app.studios import studio_steps


def has_cyrillic(s: str) -> bool:
    return any("а" <= c.lower() <= "я" or c in "ёЁ" for c in s)


@pytest.fixture
def pipeline() -> UnifiedAiPipeline:
    p = UnifiedAiPipeline()
    p.reset()
    return p


class TestUnifiedPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline_image(self, pipeline: UnifiedAiPipeline):
        task = await pipeline.run(
            AiTaskRequest(
                owner_id="owner:1",
                modality="image",
                prompt="баннер салона",
                channel="telegram",
                meta={"size": "1080×1080", "style": "Минимализм"},
                studio_id="image",
            )
        )
        assert task.status == AiTaskStatus.DONE.value
        assert task.provider_id
        assert task.platform_job_id
        assert task.credits_reserved > 0
        assert task.result.get("via") in ("unified_ai_pipeline", "provider_manager")
        assert task.result.get("pipeline_version") in ("43.1", "43.2", "43.3") or task.result.get("cost_breakdown") is not None
        assert any(h["event"] == "queue" for h in task.history)

    @pytest.mark.asyncio
    async def test_cache_hit_on_repeat(self, pipeline: UnifiedAiPipeline):
        req = AiTaskRequest(owner_id="o2", modality="text", prompt="одинаковый запрос кэш")
        first = await pipeline.run(req)
        second = await pipeline.run(req)
        assert first.status == AiTaskStatus.DONE.value
        assert second.cache_hit is True
        assert second.status == AiTaskStatus.DONE.value

    @pytest.mark.asyncio
    async def test_video_voice_prompt_modalities(self, pipeline: UnifiedAiPipeline):
        for mod in ("video", "voice", "prompt", "document", "presentation", "ads"):
            t = await pipeline.run(
                AiTaskRequest(owner_id="o3", modality=mod, prompt=f"тест {mod}")
            )
            assert t.status == AiTaskStatus.DONE.value

    def test_provider_catalog_no_hardcode_in_channels(self):
        assert "openai_image" in PROVIDER_CATALOG["image"]
        assert "google_veo" in PROVIDER_CATALOG["video"]
        assert "elevenlabs_voice" in PROVIDER_CATALOG["voice"]
        assert "anthropic_text" in PROVIDER_CATALOG["text"]

    @pytest.mark.asyncio
    async def test_history_favorite_search_delete(self, pipeline: UnifiedAiPipeline):
        t = await pipeline.run(AiTaskRequest(owner_id="o4", modality="image", prompt="логотип синий"))
        pipeline.toggle_favorite(t.id)
        assert pipeline.favorites("o4")
        assert pipeline.search("o4", "логотип")
        assert pipeline.delete(t.id, "o4") is True
        assert pipeline.get(t.id) is None

    def test_owner_dashboard(self, pipeline: UnifiedAiPipeline):
        dash = pipeline.owner_dashboard("empty")
        assert "active_tasks" in dash
        assert dash["pipeline_version"] in ("43.1", "43.2", "43.3")

    @pytest.mark.asyncio
    async def test_retry_and_duplicate(self, pipeline: UnifiedAiPipeline):
        t = await pipeline.run(AiTaskRequest(owner_id="o5", modality="text", prompt="черновик"))
        dup = pipeline.duplicate(t.id)
        assert dup.id != t.id
        retried = await pipeline.retry(t.id)
        assert retried.status == AiTaskStatus.DONE.value


class TestPromptEngine:
    def test_optimize_domains(self):
        eng = PromptEngine()
        out = eng.optimize("акция на стрижку", domain="beauty", modality="image")
        assert "beauty" in out["optimized_prompt"].lower() or "красот" in out["optimized_prompt"].lower()
        assert out["idea"] == "акция на стрижку"
        for domain in ("auto", "legal", "crypto", "agro", "crm", "erp", "ads", "video"):
            r = eng.optimize("идея", domain=domain, modality="text")
            assert r["optimized_prompt"]


class TestTelegramStudio43_1:
    def test_studio_menu_labels(self):
        labels = [o.label for o in AI_STUDIO_OPTIONS]
        for required in (
            "🎨 Создать изображение",
            "🎥 Создать видео",
            "🎙 Озвучить текст",
            "💡 Улучшить промпт",
            "📢 Создать рекламу",
            "📱 Создать Reels",
            "📄 Создать документ",
            "📊 Создать презентацию",
            "📚 История",
            "⭐ Избранное",
        ):
            assert required in labels

    def test_ai_studio_keyboard_ru(self):
        kb = ai_studio_keyboard()
        flat = [b.text for row in kb.keyboard for b in row]
        assert "🎨 Создать изображение" in flat
        assert "📚 История" in flat
        assert all(
            has_cyrillic(t) or "AI" in t or "Reels" in t or t.startswith("⚙") or t.startswith("⬅")
            for t in flat
        )

    def test_developer_menu_owner_only_ru(self):
        assert BTN.DEVELOPER == "⚙ Для разработчика"
        kb = developer_menu_keyboard()
        flat = [b.text for row in kb.keyboard for b in row]
        assert "Конструктор платформы" in flat
        assert "Консоль разработчика" in flat
        assert "Platform Builder" not in flat

    def test_beauty_products(self):
        assert any("До" in p and "После" in p for p in BEAUTY_STUDIO_PRODUCTS)
        assert "Маркетинговый календарь" in BEAUTY_STUDIO_PRODUCTS
        steps = studio_steps("beauty")
        assert steps[0]["choices"]

    def test_video_steps_include_fps(self):
        ids = [s["id"] for s in studio_steps("video")]
        assert "fps" in ids
        assert "format" in ids

    @pytest.mark.asyncio
    async def test_telegram_service_uses_pipeline(self, pipeline: UnifiedAiPipeline):
        svc = TelegramAiSuperApp(pipeline=pipeline)
        assert svc.VERSION in ("43.1", "43.2", "43.3", "43.4")
        task = await svc.run_generation(
            "tg:7",
            studio_id="image",
            answers={
                "what": "баннер",
                "size": "1024×1024",
                "style": "Реализм",
                "platform": "Instagram",
                "count": "1",
                "quality": "Стандарт",
            },
        )
        assert task.result.get("via") in ("unified_ai_pipeline", "provider_manager")
        dash = svc.owner_dashboard_text("tg:7")
        assert "Дашборд" in dash

    def test_main_menu_unchanged_simple(self):
        assert len(MAIN_MENU_BUTTONS) == 12
        assert any(b.id == "ai_command" for b in MAIN_MENU_BUTTONS)
        assert any(b.id == "work_mode" for b in MAIN_MENU_BUTTONS)
        assert any(b.id == "memory" for b in MAIN_MENU_BUTTONS)
        assert any(b.id == "automation" for b in MAIN_MENU_BUTTONS)


def test_pipeline_export_from_platform_ai():
    from platform_ai import unified_ai_pipeline as exported

    assert exported.VERSION in ("43.1", "43.2", "43.3")
