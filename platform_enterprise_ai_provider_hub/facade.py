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
        route = self.router.route(task_type="general_chat", models=[m1, m2, m3], prefer_quality=True)
        fb = self.fallback.execute(
            chain=[
                {"provider_id": "prov_openai", "model_id": "gpt-4o-mini"},
                {"provider_id": "prov_anthropic", "model_id": "claude-haiku"},
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
            allowed_models=["gpt-4o-mini", "claude-haiku", "corp-llm"],
            actor="platform_owner",
            action="bootstrap",
        )
        links = self.integrations.link()
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
                "providers": [openai, anthropic, local],
                "models": [m1, m2, m3],
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
