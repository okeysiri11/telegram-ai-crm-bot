# AI Marketplace & Plugin Store — Sprint 12.1.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MarketplaceConfig:
    application_name: str = "AI Marketplace"
    application: str = "marketplace"
    application_version: str = "3.1.0-alpha"
    release_status: str = "Marketplace Alpha"
    platform_dependency: str = "AI Platform Core v3.0"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    ai_ecosystem_dependency: str = "Unified AI Ecosystem 3.0"
    api_version: str = "v1"
    api_prefix: str = "/api/marketplace/v1"
    internal_prefix: str = "/internal/marketplace/v1"
    marketplace_core: str = "1.0"
    plugin_store: str = "1.0"
    ai_marketplace: str = "1.0"
    workflow_marketplace: str = "1.0"
    connector_marketplace: str = "1.0"
    security: str = "1.0"
    developer_portal: str = "1.0"
    enterprise_marketplace: str = "1.0"
    categories: list[str] = field(
        default_factory=lambda: [
            "crm",
            "erp",
            "accounting",
            "legal",
            "construction",
            "drone",
            "auto",
            "agro",
            "manufacturing",
            "finance",
            "logistics",
            "healthcare",
            "education",
            "retail",
            "hospitality",
            "custom_enterprise",
        ]
    )


DEFAULT_CONFIG = MarketplaceConfig()
