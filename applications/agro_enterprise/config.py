# Agro Enterprise Platform — Sprint 14.3 Crop AI.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgroEnterpriseConfig:
    application_name: str = "Agro Enterprise Platform"
    application: str = "agro_enterprise"
    application_version: str = "4.3.3-enterprise"
    release_status: str = "Crop AI"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v4.3.2-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/agro-enterprise/v1"
    precision_agriculture_api_prefix: str = "/api/precision-agriculture/v1"
    smart_irrigation_api_prefix: str = "/api/smart-irrigation/v1"
    crop_ai_api_prefix: str = "/api/crop-ai/v1"
    internal_prefix: str = "/internal/agro-enterprise/v1"
    agro_marketplace: str = "1.0"
    farm_registry: str = "1.0"
    crop_management: str = "1.0"
    agro_crm: str = "1.0"
    knowledge: str = "1.0"
    analytics: str = "1.0"
    precision_agriculture: str = "1.0"
    smart_irrigation: str = "1.0"
    crop_ai: str = "1.0"
    listing_categories: list[str] = field(
        default_factory=lambda: ["crops", "seeds", "fertilizers", "equipment", "services"]
    )
    crm_types: list[str] = field(default_factory=lambda: ["farmer", "supplier", "buyer"])
    knowledge_bases: list[str] = field(
        default_factory=lambda: ["crop", "soil", "equipment", "regulations"]
    )
    dashboard_types: list[str] = field(
        default_factory=lambda: ["marketplace", "farm", "production", "sales", "executive"]
    )


DEFAULT_CONFIG = AgroEnterpriseConfig()
