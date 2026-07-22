# Auto Marketplace configuration — Sprint 13.3 Dealer CRM.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AutoMarketplaceConfig:
    application_name: str = "Auto Marketplace Enterprise Platform"
    api_version: str = "v1"
    api_prefix: str = "/api/auto/v1"
    enterprise_api_prefix: str = "/api/auto-marketplace/v1"
    vin_intelligence_api_prefix: str = "/api/vin-intelligence/v1"
    inspection_ai_api_prefix: str = "/api/inspection-ai/v1"
    dealer_crm_api_prefix: str = "/api/dealer-crm/v1"
    internal_prefix: str = "/internal/auto/v1"
    webhook_prefix: str = "/webhooks/auto/v1"
    default_currency: str = "USD"
    enable_ai_recommendations: bool = True
    enable_auctions: bool = True
    application_version: str = "4.1.3-enterprise"
    release_status: str = "Dealer CRM"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v4.1.2-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    enterprise_automotive_suite: str = "1.0"
    vin_intelligence: str = "1.0"
    inspection_ai: str = "1.0"
    dealer_crm: str = "1.0"
    vehicle_types: list[str] = field(
        default_factory=lambda: [
            "car",
            "motorcycle",
            "truck",
            "commercial",
            "special_equipment",
            "electric",
            "hybrid",
        ]
    )
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
