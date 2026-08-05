# Extended provider catalog — Sprint 31.2 Integration Hub deepen.
# Declarative registry only; connectors implement gradually. Runtime = SoR.

from __future__ import annotations

from typing import Any

# Categories mirror the Enterprise Integration Hub brief.
PROVIDER_CATEGORIES = (
    "ai",
    "image",
    "video",
    "audio",
    "automation",
    "crm",
    "storage",
    "payments",
    "observability",
    "security",
    "orchestration",
)

EXTENDED_PROVIDER_CATALOG: dict[str, dict[str, Any]] = {
    # —— AI ——
    "openai": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "https://api.openai.com/v1"},
    "anthropic": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "https://api.anthropic.com"},
    "google_gemini": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "https://generativelanguage.googleapis.com"},
    "openrouter": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "https://openrouter.ai/api/v1"},
    "deepseek": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "https://api.deepseek.com"},
    "mistral": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "https://api.mistral.ai"},
    "groq": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "https://api.groq.com/openai/v1"},
    "xai": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "https://api.x.ai/v1"},
    "ollama": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "http://localhost:11434"},
    "litellm": {"category": "ai", "implemented": True, "via": "aph", "endpoint": "http://localhost:4000", "role": "gateway"},
    # —— Image ——
    "openai_images": {"category": "image", "implemented": False, "via": "aph"},
    "flux": {"category": "image", "implemented": False, "via": "aph"},
    "stable_diffusion": {"category": "image", "implemented": False, "via": "aph"},
    "ideogram": {"category": "image", "implemented": False, "via": "aph"},
    "recraft": {"category": "image", "implemented": False, "via": "aph"},
    "fal_ai": {"category": "image", "implemented": False, "via": "aph"},
    "comfyui": {"category": "image", "implemented": False, "via": "local"},
    "automatic1111": {"category": "image", "implemented": False, "via": "local"},
    # —— Video ——
    "runway": {"category": "video", "implemented": False, "via": "aph"},
    "kling": {"category": "video", "implemented": False, "via": "aph"},
    "pika": {"category": "video", "implemented": False, "via": "aph"},
    "luma": {"category": "video", "implemented": False, "via": "aph"},
    "veo": {"category": "video", "implemented": False, "via": "aph"},
    "minimax": {"category": "video", "implemented": False, "via": "aph"},
    # —— Audio ——
    "elevenlabs": {"category": "audio", "implemented": False, "via": "aph"},
    "cartesia": {"category": "audio", "implemented": False, "via": "aph"},
    "openai_voice": {"category": "audio", "implemented": False, "via": "aph"},
    "azure_speech": {"category": "audio", "implemented": False, "via": "aph"},
    "whisper": {"category": "audio", "implemented": True, "via": "aph"},
    # —— Automation ——
    "telegram": {"category": "automation", "implemented": True, "via": "platform_integrations"},
    "whatsapp": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "discord": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "slack": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "email": {"category": "automation", "implemented": True, "via": "platform_integrations"},
    "sms": {"category": "automation", "implemented": True, "via": "platform_integrations"},
    "google_calendar": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "google_drive": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "google_docs": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "microsoft_365": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "notion": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "github": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "gitlab": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "jira": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    "linear": {"category": "automation", "implemented": False, "via": "platform_integrations"},
    # —— CRM ——
    "hubspot": {"category": "crm", "implemented": False, "via": "platform_integrations"},
    "salesforce": {"category": "crm", "implemented": False, "via": "platform_integrations"},
    "bitrix24": {"category": "crm", "implemented": False, "via": "platform_integrations"},
    "pipedrive": {"category": "crm", "implemented": False, "via": "platform_integrations"},
    "zoho": {"category": "crm", "implemented": False, "via": "platform_integrations"},
    # —— Storage ——
    "s3": {"category": "storage", "implemented": False, "via": "platform_integrations"},
    "minio": {"category": "storage", "implemented": False, "via": "platform_integrations"},
    "cloudflare_r2": {"category": "storage", "implemented": False, "via": "platform_integrations"},
    "dropbox": {"category": "storage", "implemented": False, "via": "platform_integrations"},
    "onedrive": {"category": "storage", "implemented": False, "via": "platform_integrations"},
    # —— Payments ——
    "stripe": {"category": "payments", "implemented": False, "via": "platform_integrations"},
    "wayforpay": {"category": "payments", "implemented": False, "via": "platform_integrations"},
    "liqpay": {"category": "payments", "implemented": False, "via": "platform_integrations"},
    "fondy": {"category": "payments", "implemented": False, "via": "platform_integrations"},
    "paypal": {"category": "payments", "implemented": False, "via": "platform_integrations"},
    "crypto_wallets": {"category": "payments", "implemented": False, "via": "platform_integrations"},
    # —— Observability ——
    "grafana": {"category": "observability", "implemented": False, "via": "enterprise_obs"},
    "prometheus": {"category": "observability", "implemented": False, "via": "enterprise_obs"},
    "loki": {"category": "observability", "implemented": False, "via": "enterprise_obs"},
    "sentry": {"category": "observability", "implemented": False, "via": "enterprise_obs"},
    "opentelemetry": {"category": "observability", "implemented": False, "via": "enterprise_obs"},
    # —— Orchestration ——
    "n8n": {
        "category": "orchestration",
        "implemented": True,
        "via": "n8n_bridge",
        "role": "external_workflow_orchestrator",
        "system_of_record": "platform_runtime",
        "business_logic": False,
    },
}


def list_providers(*, category: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for provider_id, meta in EXTENDED_PROVIDER_CATALOG.items():
        if category and meta.get("category") != category:
            continue
        rows.append({"provider_id": provider_id, **meta})
    return rows


def get_provider(provider_id: str) -> dict[str, Any] | None:
    meta = EXTENDED_PROVIDER_CATALOG.get(provider_id)
    if not meta:
        return None
    return {"provider_id": provider_id, **meta}


def catalog_summary() -> dict[str, Any]:
    by_cat: dict[str, int] = {}
    implemented = 0
    for meta in EXTENDED_PROVIDER_CATALOG.values():
        cat = str(meta.get("category") or "other")
        by_cat[cat] = by_cat.get(cat, 0) + 1
        if meta.get("implemented"):
            implemented += 1
    return {
        "total": len(EXTENDED_PROVIDER_CATALOG),
        "implemented": implemented,
        "by_category": by_cat,
        "categories": list(PROVIDER_CATEGORIES),
        "credential_vault": "enterprise_esh",
        "ai_gateway": "enterprise_aph",
        "orchestrator": "n8n (external)",
        "system_of_record": "platform_runtime",
    }
