# Agro Marketplace configuration — Sprint 8.8 Commercial Release.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgroMarketplaceConfig:
    application_name: str = "Agro Marketplace"
    application_version: str = "2.0.0"
    application_status: str = "Production Ready"
    release: str = "Commercial"
    platform_dependency: str = "AI Platform Core v3.0"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/agro/v1"
    internal_prefix: str = "/internal/agro/v1"
    webhook_prefix: str = "/webhooks/agro/v1"
    mobile_prefix: str = "/api/agro/mobile/v1"
    partner_prefix: str = "/api/agro/partner/v1"
    default_currency: str = "USD"
    enable_ai_recommendations: bool = True
    enable_export: bool = True
    catalog_layer: str = "1.0"
    warehouse_layer: str = "1.0"
    inventory_layer: str = "1.0"
    harvest_layer: str = "1.0"
    crm_layer: str = "1.0"
    marketplace_layer: str = "1.0"
    trading_layer: str = "1.0"
    negotiation_layer: str = "1.0"
    agro_ai: str = "1.0"
    export_engine: str = "1.0"
    analytics_engine: str = "1.0"
    portal_engine: str = "1.0"


DEFAULT_CONFIG = AgroMarketplaceConfig()
