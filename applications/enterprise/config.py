# AI Ecosystem Enterprise Edition — Sprint 12.5.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnterpriseConfig:
    application_name: str = "AI Ecosystem Enterprise Edition"
    application: str = "enterprise"
    application_version: str = "4.0.0-enterprise"
    release_status: str = "Enterprise Edition"
    platform_dependency: str = "AI Platform Core v3.0"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/enterprise/v1"
    internal_prefix: str = "/internal/enterprise/v1"
    enterprise_platform: str = "1.0"
    enterprise_administration: str = "1.0"
    enterprise_ai: str = "1.0"
    enterprise_services: str = "1.0"
    enterprise_infrastructure: str = "1.0"
    analytics: str = "1.0"
    knowledge: str = "1.0"
    ai_roles: list[str] = field(
        default_factory=lambda: [
            "chief",
            "department",
            "project",
            "business",
            "executive",
            "knowledge",
            "engineering",
            "analytics",
        ]
    )
    auth_providers: list[str] = field(
        default_factory=lambda: ["sso", "ldap", "active_directory", "oauth"]
    )
    report_types: list[str] = field(
        default_factory=lambda: [
            "enterprise",
            "business_intelligence",
            "executive",
            "financial",
            "operational",
            "ai_analytics",
            "predictive",
        ]
    )
    knowledge_centers: list[str] = field(
        default_factory=lambda: [
            "wiki",
            "architecture",
            "developer",
            "operations",
            "executive",
        ]
    )


DEFAULT_CONFIG = EnterpriseConfig()
