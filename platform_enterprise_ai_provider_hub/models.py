"""AI Provider Hub constants — Sprint 24.9."""

from __future__ import annotations

PROVIDER_KINDS = (
    "openai",
    "anthropic",
    "google_gemini",
    "mistral",
    "xai",
    "deepseek",
    "ollama",
    "vllm",
    "lm_studio",
    "azure_openai",
    "aws_bedrock",
    "local_corporate",
    "openrouter",
    "groq",
    "litellm",
)

PROVIDER_STATUSES = ("active", "degraded", "offline", "disabled")

MODEL_TYPES = ("chat", "embedding", "vision", "audio", "reasoning", "code")

TASK_TYPES = (
    "general_chat",
    "reasoning",
    "code",
    "summarization",
    "extraction",
    "embedding",
    "vision",
    "cheap_batch",
    "secure_local",
)

ROUTE_CRITERIA = (
    "task_type",
    "cost",
    "speed",
    "quality",
    "availability",
    "company_policy",
    "security_requirements",
)

INTEGRATION_TARGETS = (
    "enterprise_ai_orchestrator",
    "workflow_intelligence",
    "learning_engine",
    "enterprise_knowledge_graph",
    "strategy_intelligence",
    "product_intelligence",
    "ai_marketing_os",
    "beauty_os",
    "commerce_core",
    "communications_hub",
)

KPI_TARGETS = {
    "unified_ai_gateway": True,
    "unified_model_registry": True,
    "intelligent_model_selection": True,
    "automatic_fallback": True,
    "usage_analytics": True,
    "cost_control": True,
    "provider_independence": True,
}

PRINCIPLES = (
    "no_direct_provider_calls",
    "single_ai_router",
    "extensible_providers",
    "logged_fallbacks",
    "secrets_never_in_modules",
    "cost_and_policy_aware",
    "no_duplicated_business_logic",
)
