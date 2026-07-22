# Auto Marketplace configuration — Sprint 10.1 Foundation.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AutoMarketplaceConfig:
    application_name: str = "Auto Marketplace"
    api_version: str = "v1"
    api_prefix: str = "/api/auto/v1"
    internal_prefix: str = "/internal/auto/v1"
    webhook_prefix: str = "/webhooks/auto/v1"
    default_currency: str = "USD"
    enable_ai_recommendations: bool = True
    enable_auctions: bool = True
    application_version: str = "1.0.0-alpha"
    release_status: str = "Foundation Alpha"
    platform_dependency: str = "AI Platform Core v3"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    mobile_api_prefix: str = "/api/auto/mobile/v1"
    partner_api_prefix: str = "/api/auto/partner/v1"
    portal_prefix: str = "/api/auto/v1/portal"
    catalog_engine: str = "1.0"
    crm_foundation: str = "1.0"


DEFAULT_CONFIG = AutoMarketplaceConfig()
