# Unified AI Ecosystem Integration — Sprint 12.0.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UnifiedEcosystemConfig:
    application_name: str = "Unified AI Ecosystem"
    application: str = "ai_ecosystem"
    application_version: str = "3.0.0-alpha"
    release_status: str = "Unified Integration Alpha"
    platform_dependency: str = "AI Platform Core v3.0"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/ai-ecosystem/v1"
    internal_prefix: str = "/internal/ai-ecosystem/v1"
    ecosystem_manager: str = "1.0"
    application_registry: str = "1.0"
    unified_ai: str = "1.0"
    shared_memory: str = "1.0"
    cross_app_communication: str = "1.0"
    unified_auth: str = "1.0"
    unified_dashboard: str = "1.0"
    unified_search: str = "1.0"
    global_knowledge: str = "1.0"
    analytics: str = "1.0"
    registered_applications: list[str] = field(
        default_factory=lambda: [
            "crm",
            "auto_marketplace",
            "agro_marketplace",
            "port_erp",
            "drone_platform",
            "platform_core",
            "knowledge_system",
        ]
    )


DEFAULT_CONFIG = UnifiedEcosystemConfig()
