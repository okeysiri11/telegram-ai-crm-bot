# Auto Marketplace configuration — Sprint 10.8 Commercial Release 2.0.0.

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
    application_version: str = "2.0.0"
    release_status: str = "Commercial Release"
    platform_dependency: str = "AI Platform Core v3"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    mobile_api_prefix: str = "/api/auto/mobile/v1"
    partner_api_prefix: str = "/api/auto/partner/v1"
    portal_prefix: str = "/api/auto/v1/portal"
    catalog_engine: str = "1.0"
    crm_foundation: str = "1.0"
    vin_engine: str = "1.0"
    dealer_engine: str = "1.0"
    auto_ai_engine: str = "1.0"
    recommendation_engine: str = "1.0"
    transaction_engine: str = "1.0"
    auction_engine: str = "1.0"
    finance_engine: str = "1.0"
    insurance_engine: str = "1.0"
    service_engine: str = "1.0"
    parts_engine: str = "1.0"
    maintenance_engine: str = "1.0"
    transport_engine: str = "1.0"
    tracking_engine: str = "1.0"
    customs_engine: str = "1.0"
    fleet_engine: str = "1.0"
    rental_engine: str = "1.0"
    operations_engine: str = "1.0"
    enterprise_engine: str = "1.0"
    global_network: str = "1.0"
    production_ready: bool = True


DEFAULT_CONFIG = AutoMarketplaceConfig()
