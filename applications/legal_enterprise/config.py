# Legal Enterprise Platform — Sprint 17.0 Foundation.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LegalEnterpriseConfig:
    application_name: str = "Legal Intelligence Platform"
    application: str = "legal_enterprise"
    application_version: str = "4.9.0-enterprise"
    release_status: str = "Legal Enterprise Foundation"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v4.8.0-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/legal-enterprise/v1"
    internal_prefix: str = "/internal/legal-enterprise/v1"
    legal_registry: str = "1.0"
    legislation_registry: str = "1.0"
    court_infrastructure: str = "1.0"
    case_management: str = "1.0"
    knowledge: str = "1.0"
    analytics: str = "1.0"
    legal_roles: list[str] = field(
        default_factory=lambda: [
            "plaintiff",
            "defendant",
            "counsel",
            "prosecutor",
            "judge",
            "clerk",
            "witness",
            "expert",
        ]
    )
    court_levels: list[str] = field(
        default_factory=lambda: ["regional", "appeal", "supreme"]
    )
    case_statuses: list[str] = field(
        default_factory=lambda: [
            "draft",
            "filed",
            "in_progress",
            "hearing",
            "appealed",
            "closed",
            "archived",
        ]
    )
    legislation_types: list[str] = field(
        default_factory=lambda: [
            "constitution",
            "civil",
            "commercial",
            "criminal",
            "administrative",
            "tax",
            "labor",
            "treaty",
        ]
    )
    dashboard_types: list[str] = field(
        default_factory=lambda: ["legal", "case", "court", "legislation"]
    )
    knowledge_bases: list[str] = field(
        default_factory=lambda: ["law", "court", "case", "document"]
    )


DEFAULT_CONFIG = LegalEnterpriseConfig()
