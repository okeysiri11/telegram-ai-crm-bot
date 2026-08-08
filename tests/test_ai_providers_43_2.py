"""Sprint 43.2 — Real AI Providers, Multimodal & Connectors."""

from __future__ import annotations

import pytest

from platform_ai.multimodal import MultimodalPipeline, MULTIMODAL_STEPS
from platform_ai.pipeline import UnifiedAiPipeline
from platform_ai.pipeline_models import AiTaskRequest
from platform_ai.providers.manager import ProviderManager
from platform_ai.providers.vault import ProviderKeyVault, PROVIDER_KEY_NAMES
from platform_security.secrets.manager import SecretManager
from services.telegram_ai_super_app.concierge import plan_from_text
from services.telegram_ai_super_app.keyboards import post_generation_inline
from services.telegram_ai_super_app.studios import BEAUTY_SCENARIOS, beauty_brief_steps


@pytest.fixture
def vault() -> ProviderKeyVault:
    sm = SecretManager()
    v = ProviderKeyVault(secrets=sm)
    return v


@pytest.fixture
def manager(vault: ProviderKeyVault) -> ProviderManager:
    return ProviderManager(vault=vault)


class TestProviderManager:
    def test_catalog_has_required_vendors(self, manager: ProviderManager):
        ids = {p.id for p in manager.list()}
        for required in (
            "openai_image",
            "flux_image",
            "recraft_image",
            "ideogram_image",
            "bfl_image",
            "stability_image",
            "fal_image",
            "replicate_image",
            "runway_video",
            "google_veo",
            "pika_video",
            "kling_video",
            "luma_video",
            "hailuo_video",
            "elevenlabs_voice",
            "cartesia_voice",
            "google_tts",
            "azure_speech",
            "openai_voice",
            "openai_text",
            "anthropic_text",
            "gemini_text",
            "deepseek_text",
            "mistral_text",
        ):
            assert required in ids

    def test_provider_def_fields(self, manager: ProviderManager):
        p = manager.get("openai_image")
        assert p is not None
        d = p.to_dict()
        for key in ("id", "name", "type", "api", "cost_unit", "limits", "status", "fallback", "timeout_sec", "retry"):
            assert key in d

    def test_key_vault_store_and_status(self, vault: ProviderKeyVault):
        vault.store("openai", "sk-test-not-real")
        assert vault.has("openai")
        status = vault.list_status()
        assert any(s["vendor"] == "openai" and s["configured"] for s in status)
        assert "openai" in PROVIDER_KEY_NAMES

    @pytest.mark.asyncio
    async def test_generate_sandbox_with_fallback(self, manager: ProviderManager):
        # Force preferred unavailable → fallback to local
        manager.get("openai_image").status = "disabled"  # type: ignore[union-attr]
        result = await manager.generate("image", "тест баннер", preferred="openai_image")
        assert result.modality == "image"
        assert result.mode in ("sandbox", "live")
        assert result.cost.total >= 0
        assert result.tried

    @pytest.mark.asyncio
    async def test_health_check(self, manager: ProviderManager):
        rows = await manager.health_check("local_image")
        assert rows
        assert rows[0].provider_id == "local_image"

    def test_enterprise_analytics(self, manager: ProviderManager):
        snap = manager.enterprise_analytics()
        assert snap["providers_total"] >= 20
        assert "by_type" in snap


class TestMultimodal:
    @pytest.mark.asyncio
    async def test_multimodal_chain(self, manager: ProviderManager):
        pipe = MultimodalPipeline(providers=manager)
        out = await pipe.run("реклама салона красоты", owner_id="o1")
        assert out["steps"] == list(MULTIMODAL_STEPS)
        assert "llm" in out["artifacts"]
        assert "image" in out["artifacts"]
        assert "video" in out["artifacts"]
        assert "voice" in out["artifacts"]
        assert "publishing" in out["artifacts"]
        assert out["total_cost"] >= 0


class TestPipelineIntegration:
    @pytest.mark.asyncio
    async def test_pipeline_uses_provider_manager(self, manager: ProviderManager):
        pipeline = UnifiedAiPipeline(providers=manager)
        pipeline.reset()
        task = await pipeline.run(
            AiTaskRequest(owner_id="u1", modality="image", prompt="логотип")
        )
        assert task.status == "готово"
        assert task.result.get("via") == "provider_manager"
        assert "cost_breakdown" in task.result
        assert task.result.get("mode") in ("sandbox", "live")


class TestTelegram43_2:
    def test_beauty_scenarios(self):
        assert "Подарочный сертификат" in BEAUTY_SCENARIOS
        assert "До / После" in BEAUTY_SCENARIOS or "До/После" in BEAUTY_SCENARIOS
        assert "Ответ в Telegram" in BEAUTY_SCENARIOS
        steps = beauty_brief_steps()
        assert len(steps[0]["choices"]) >= 10

    def test_post_gen_ux_buttons(self):
        kb = post_generation_inline("job123")
        flat = [b.text for row in kb.inline_keyboard for b in row]
        for label in ("📥 Скачать", "🔄 Повторить", "✏ Изменить", "❤️ В избранное", "🎥 Видео", "🎤 Озвучка"):
            assert label in flat

    def test_owner_ai_routing(self):
        plan = plan_from_text("Покажи прибыль")
        assert plan.intent == "owner_ai"
        plan2 = plan_from_text("Создай лендинг")
        assert plan2.intent == "owner_ai"
