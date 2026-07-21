# Agro Marketplace configuration — Sprint 8.1.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgroMarketplaceConfig:
    application_name: str = "Agro Marketplace"
    application_version: str = "1.0.0-alpha"
    platform_dependency: str = "AI Platform Core v3.0"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/agro/v1"
    internal_prefix: str = "/internal/agro/v1"
    webhook_prefix: str = "/webhooks/agro/v1"
    default_currency: str = "USD"
    enable_ai_recommendations: bool = True
    enable_export: bool = True


DEFAULT_CONFIG = AgroMarketplaceConfig()
