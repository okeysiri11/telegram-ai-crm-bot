# Port Enterprise Platform — Sprint 15.3 Multimodal Logistics.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PortEnterpriseConfig:
    application_name: str = "Port Enterprise Platform"
    application: str = "port_enterprise"
    application_version: str = "4.5.3-enterprise"
    release_status: str = "Multimodal Logistics"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v4.5.2-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/port-enterprise/v1"
    navigation_api_prefix: str = "/api/port-navigation/v1"
    container_management_api_prefix: str = "/api/port-containers/v1"
    multimodal_logistics_api_prefix: str = "/api/port-multimodal/v1"
    internal_prefix: str = "/internal/port-enterprise/v1"
    port_registry: str = "1.0"
    terminal_management: str = "1.0"
    cargo_management: str = "1.0"
    shipping_companies: str = "1.0"
    fleet_registry: str = "1.0"
    port_operations: str = "1.0"
    navigation: str = "1.0"
    container_management: str = "1.0"
    multimodal_logistics: str = "1.0"
    knowledge: str = "1.0"
    analytics: str = "1.0"
    terminal_types: list[str] = field(
        default_factory=lambda: ["container", "bulk", "liquid", "roro", "passenger"]
    )
    cargo_categories: list[str] = field(
        default_factory=lambda: ["general", "hazardous", "oversized", "refrigerated", "bulk", "liquid"]
    )
    dashboard_types: list[str] = field(
        default_factory=lambda: ["port", "terminal", "cargo", "fleet", "operations"]
    )
    knowledge_bases: list[str] = field(
        default_factory=lambda: ["port", "terminal", "fleet", "cargo", "shipping"]
    )


DEFAULT_CONFIG = PortEnterpriseConfig()
