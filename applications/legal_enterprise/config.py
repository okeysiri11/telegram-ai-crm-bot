# Legal Enterprise Platform — Sprint 17.2 Judicial Intelligence.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LegalEnterpriseConfig:
    application_name: str = "Legal Intelligence Platform"
    application: str = "legal_enterprise"
    application_version: str = "4.9.2-enterprise"
    release_status: str = "Judicial Intelligence"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v4.9.1-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/legal-enterprise/v1"
    legislation_intelligence_api_prefix: str = "/api/legal-li/v1"
    judicial_intelligence_api_prefix: str = "/api/legal-ji/v1"
    internal_prefix: str = "/internal/legal-enterprise/v1"
    legal_registry: str = "1.0"
    legislation_registry: str = "1.0"
    court_infrastructure: str = "1.0"
    case_management: str = "1.0"
    legislation_intelligence: str = "1.0"
    judicial_intelligence: str = "1.0"
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
    li_repository_types: list[str] = field(
        default_factory=lambda: [
            "constitution",
            "code",
            "law",
            "regulation",
            "government_resolution",
            "ministerial_order",
            "international_treaty",
            "local_regulation",
        ]
    )
    li_law_classes: list[str] = field(
        default_factory=lambda: ["constitutional", "statutory", "regulatory", "soft_law"]
    )
    li_industries: list[str] = field(
        default_factory=lambda: [
            "technology",
            "finance",
            "healthcare",
            "energy",
            "transport",
            "agriculture",
            "general",
        ]
    )
    li_topics: list[str] = field(
        default_factory=lambda: [
            "privacy",
            "contracts",
            "tax",
            "labor",
            "criminal",
            "environment",
            "governance",
        ]
    )
    li_dashboard_types: list[str] = field(
        default_factory=lambda: ["legislation", "regulation", "legal_search", "ai_analysis"]
    )
    li_knowledge_bases: list[str] = field(
        default_factory=lambda: ["legislation", "regulation", "article", "reference"]
    )
    ji_decision_types: list[str] = field(
        default_factory=lambda: ["judgment", "ruling", "order", "opinion"]
    )
    ji_case_classes: list[str] = field(
        default_factory=lambda: [
            "civil",
            "commercial",
            "criminal",
            "administrative",
            "appellate",
            "constitutional",
        ]
    )
    ji_topics: list[str] = field(
        default_factory=lambda: [
            "contracts",
            "privacy",
            "tax",
            "labor",
            "property",
            "appeals",
            "commercial",
        ]
    )
    ji_dashboard_types: list[str] = field(
        default_factory=lambda: ["court", "decision", "judge", "ai_judicial"]
    )
    ji_knowledge_bases: list[str] = field(
        default_factory=lambda: ["judicial", "decision", "judge", "court", "case_law"]
    )


DEFAULT_CONFIG = LegalEnterpriseConfig()
