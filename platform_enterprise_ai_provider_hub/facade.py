"""AI Provider Hub library facade — Sprint 24.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_ai_provider_hub.analytics import AIUsageAnalytics
from platform_enterprise_ai_provider_hub.cost import CostOptimization
from platform_enterprise_ai_provider_hub.fallback import FallbackEngine
from platform_enterprise_ai_provider_hub.integrations import ProviderHubIntegrations
from platform_enterprise_ai_provider_hub.models import PRINCIPLES, PROVIDER_KINDS
from platform_enterprise_ai_provider_hub.models_registry import ModelRegistry
from platform_enterprise_ai_provider_hub.prompt import PromptGateway
from platform_enterprise_ai_provider_hub.providers import AIProviderRegistry
from platform_enterprise_ai_provider_hub.router import IntelligentModelRouter
from platform_enterprise_ai_provider_hub.security import SecurityLayer


class AIProviderHubLibrary:
    def __init__(self) -> None:
        self.providers = AIProviderRegistry()
        self.models = ModelRegistry()
        self.router = IntelligentModelRouter()
        self.fallback = FallbackEngine()
        self.prompt = PromptGateway()
        self.cost = CostOptimization()
        self.analytics = AIUsageAnalytics()
        self.security = SecurityLayer()
        self.integrations = ProviderHubIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        catalog = self.providers.catalog()
        openai = self.providers.register(
            provider_id="prov_openai",
            name="OpenAI",
            kind="openai",
            endpoint="https://api.openai.com/v1",
            supported_models=["gpt-4o-mini"],
            cost_per_1k=0.15,
            priority=10,
            health_score=0.95,
        )
        anthropic = self.providers.register(
            provider_id="prov_anthropic",
            name="Anthropic",
            kind="anthropic",
            endpoint="https://api.anthropic.com",
            supported_models=["claude-haiku"],
            cost_per_1k=0.25,
            priority=20,
            health_score=0.92,
        )
        local = self.providers.register(
            provider_id="local_corporate",
            name="Corporate Local",
            kind="local_corporate",
            endpoint="http://localhost:8080/v1",
            supported_models=["corp-llm"],
            cost_per_1k=0.01,
            priority=90,
            health_score=0.88,
        )
        gemini = self.providers.register(
            provider_id="prov_gemini",
            name="Google Gemini",
            kind="google_gemini",
            endpoint="https://generativelanguage.googleapis.com",
            supported_models=["gemini-1.5-flash"],
            cost_per_1k=0.1,
            priority=25,
            health_score=0.9,
        )
        openrouter = self.providers.register(
            provider_id="prov_openrouter",
            name="OpenRouter",
            kind="openrouter",
            endpoint="https://openrouter.ai/api/v1",
            supported_models=["openrouter/auto"],
            cost_per_1k=0.12,
            priority=30,
            health_score=0.91,
        )
        deepseek = self.providers.register(
            provider_id="prov_deepseek",
            name="DeepSeek",
            kind="deepseek",
            endpoint="https://api.deepseek.com",
            supported_models=["deepseek-chat"],
            cost_per_1k=0.05,
            priority=35,
            health_score=0.89,
        )
        mistral = self.providers.register(
            provider_id="prov_mistral",
            name="Mistral",
            kind="mistral",
            endpoint="https://api.mistral.ai",
            supported_models=["mistral-small"],
            cost_per_1k=0.08,
            priority=40,
            health_score=0.9,
        )
        groq = self.providers.register(
            provider_id="prov_groq",
            name="Groq",
            kind="groq",
            endpoint="https://api.groq.com/openai/v1",
            supported_models=["llama-3.1-8b"],
            cost_per_1k=0.04,
            priority=15,
            health_score=0.93,
        )
        xai = self.providers.register(
            provider_id="prov_xai",
            name="xAI Grok",
            kind="xai",
            endpoint="https://api.x.ai/v1",
            supported_models=["grok-beta"],
            cost_per_1k=0.2,
            priority=45,
            health_score=0.87,
        )
        ollama = self.providers.register(
            provider_id="prov_ollama",
            name="Ollama",
            kind="ollama",
            endpoint="http://localhost:11434",
            supported_models=["llama3.2"],
            cost_per_1k=0.0,
            priority=85,
            health_score=0.86,
        )
        litellm = self.providers.register(
            provider_id="prov_litellm",
            name="LiteLLM Gateway",
            kind="litellm",
            endpoint="http://localhost:4000",
            supported_models=["litellm/proxy"],
            cost_per_1k=0.0,
            priority=5,
            health_score=0.94,
        )
        m1 = self.models.register(
            model_id="gpt-4o-mini",
            provider_id="prov_openai",
            quality_score=0.85,
            speed_score=0.9,
            cost_per_1k=0.15,
            capabilities=["chat", "tools"],
        )
        m2 = self.models.register(
            model_id="claude-haiku",
            provider_id="prov_anthropic",
            quality_score=0.88,
            speed_score=0.8,
            cost_per_1k=0.25,
            capabilities=["chat", "reasoning"],
        )
        m3 = self.models.register(
            model_id="corp-llm",
            provider_id="local_corporate",
            quality_score=0.7,
            speed_score=0.75,
            cost_per_1k=0.01,
            capabilities=["chat", "secure_local"],
        )
        m4 = self.models.register(
            model_id="gemini-1.5-flash",
            provider_id="prov_gemini",
            quality_score=0.84,
            speed_score=0.92,
            cost_per_1k=0.1,
            capabilities=["chat", "vision"],
        )
        m5 = self.models.register(
            model_id="llama-3.1-8b",
            provider_id="prov_groq",
            quality_score=0.78,
            speed_score=0.98,
            cost_per_1k=0.04,
            capabilities=["chat", "code"],
        )
        route = self.router.route(task_type="general_chat", models=[m1, m2, m3, m4, m5], prefer_quality=True)
        fb = self.fallback.execute(
            chain=[
                {"provider_id": "prov_litellm", "model_id": "litellm/proxy"},
                {"provider_id": "prov_openai", "model_id": "gpt-4o-mini"},
                {"provider_id": "prov_anthropic", "model_id": "claude-haiku"},
                {"provider_id": "prov_groq", "model_id": "llama-3.1-8b"},
                {"provider_id": "local_corporate", "model_id": "corp-llm"},
            ],
            fail_until=1,
        )
        prompt = self.prompt.assemble(
            template="enterprise_default",
            system_instructions="Follow company policy",
            brand_dna={"tone": "professional"},
            enterprise_context={"tenant": "demo"},
            knowledge_graph_refs=["ekg:policy"],
            security_policy={"redact_secrets": True},
            user_prompt="Summarize weekly ops",
        )
        costs = self.cost.track(
            entries=[
                {"provider_id": "prov_openai", "client_id": "c1", "agent_id": "ops_ai", "unit": "ops", "task_type": "summarization", "cost": 0.02},
                {"provider_id": "local_corporate", "client_id": "c1", "agent_id": "ops_ai", "unit": "ops", "task_type": "summarization", "cost": 0.001},
            ]
        )
        usage = self.analytics.summarize(
            requests=[
                {"success": True, "latency_ms": 120, "cost": 0.02, "quality": 0.9, "fallback_used": False, "model_id": "gpt-4o-mini"},
                {"success": True, "latency_ms": 200, "cost": 0.001, "quality": 0.75, "fallback_used": True, "model_id": "corp-llm"},
            ]
        )
        sec = self.security.protect(
            secret_ref="vault://providers/openai/api_key",
            allowed_models=["gpt-4o-mini", "claude-haiku", "corp-llm", "gemini-1.5-flash", "llama-3.1-8b"],
            actor="platform_owner",
            action="bootstrap",
        )
        links = self.integrations.link()
        providers_full = [
            openai,
            anthropic,
            local,
            gemini,
            openrouter,
            deepseek,
            mistral,
            groq,
            xai,
            ollama,
            litellm,
        ]
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "ai_provider_hub_ready": True,
            "model_router_ready": True,
            "fallback_engine_ready": True,
            "ai_cost_control_ready": True,
            "supported_provider_kinds": len(PROVIDER_KINDS),
            "direct_provider_call": False,
            "via_hub_only": True,
            "provider_independence": True,
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "catalog": catalog,
                "providers": providers_full,
                "models": [m1, m2, m3, m4, m5],
                "route": route,
                "fallback": fb,
                "prompt": prompt,
                "cost": costs,
                "analytics": usage,
                "security": sec,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "providers",
                "models",
                "router",
                "fallback",
                "prompt",
                "cost",
                "analytics",
                "security",
            ],
            "principles": self.principles(),
            "via_hub_only": True,
        }


ai_provider_hub_library = AIProviderHubLibrary()
