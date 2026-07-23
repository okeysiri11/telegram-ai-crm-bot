# Legal Enterprise Platform — Sprint 17.7 Executive Legal Intelligence.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LegalEnterpriseConfig:
    application_name: str = "Legal Intelligence Platform"
    application: str = "legal_enterprise"
    application_version: str = "4.9.7-enterprise"
    release_status: str = "Executive Legal Intelligence"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v4.9.6-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/legal-enterprise/v1"
    legislation_intelligence_api_prefix: str = "/api/legal-li/v1"
    judicial_intelligence_api_prefix: str = "/api/legal-ji/v1"
    case_management_api_prefix: str = "/api/legal-cm/v1"
    document_intelligence_api_prefix: str = "/api/legal-di/v1"
    compliance_api_prefix: str = "/api/legal-cp/v1"
    ai_legal_assistant_api_prefix: str = "/api/legal-aa/v1"
    executive_intelligence_api_prefix: str = "/api/legal-ei/v1"
    internal_prefix: str = "/internal/legal-enterprise/v1"
    legal_registry: str = "1.0"
    legislation_registry: str = "1.0"
    court_infrastructure: str = "1.0"
    case_management: str = "1.0"
    case_management_platform: str = "1.0"
    legislation_intelligence: str = "1.0"
    judicial_intelligence: str = "1.0"
    document_intelligence: str = "1.0"
    compliance: str = "1.0"
    ai_legal_assistant: str = "1.0"
    executive_intelligence: str = "1.0"
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
    cm_case_statuses: list[str] = field(
        default_factory=lambda: [
            "intake",
            "active",
            "hearing",
            "appeal",
            "settled",
            "closed",
            "archived",
        ]
    )
    cm_priorities: list[str] = field(
        default_factory=lambda: ["low", "medium", "high", "critical"]
    )
    cm_categories: list[str] = field(
        default_factory=lambda: [
            "civil",
            "commercial",
            "criminal",
            "administrative",
            "labor",
            "family",
        ]
    )
    cm_deadline_types: list[str] = field(
        default_factory=lambda: [
            "procedural",
            "limitation",
            "appeal",
            "evidence",
            "filing",
        ]
    )
    cm_dashboard_types: list[str] = field(
        default_factory=lambda: ["case", "calendar", "deadline", "workflow", "ai_case"]
    )
    cm_knowledge_bases: list[str] = field(
        default_factory=lambda: ["case", "deadline", "task", "document", "calendar"]
    )
    di_contract_types: list[str] = field(
        default_factory=lambda: ["sales", "service", "employment", "nda", "lease", "custom"]
    )
    di_clause_kinds: list[str] = field(
        default_factory=lambda: [
            "general",
            "confidentiality",
            "indemnity",
            "termination",
            "liability",
            "payment",
            "governing_law",
            "compliance",
        ]
    )
    di_formats: list[str] = field(default_factory=lambda: ["pdf", "docx", "txt", "image"])
    di_doc_classes: list[str] = field(
        default_factory=lambda: ["sales", "service", "employment", "nda", "lease", "other"]
    )
    di_dashboard_types: list[str] = field(
        default_factory=lambda: ["contract", "document", "risk", "ai_review"]
    )
    di_knowledge_bases: list[str] = field(
        default_factory=lambda: ["document", "clause", "contract", "risk", "template"]
    )
    cp_compliance_statuses: list[str] = field(
        default_factory=lambda: ["open", "in_progress", "compliant", "non_compliant", "waived"]
    )
    cp_counterparty_types: list[str] = field(
        default_factory=lambda: ["vendor", "customer", "partner", "other"]
    )
    cp_risk_levels: list[str] = field(
        default_factory=lambda: ["low", "medium", "high", "critical"]
    )
    cp_dashboard_types: list[str] = field(
        default_factory=lambda: ["compliance", "corporate", "license", "risk", "ai_compliance"]
    )
    cp_knowledge_bases: list[str] = field(
        default_factory=lambda: ["compliance", "corporate", "license", "policy", "risk"]
    )
    aa_research_modes: list[str] = field(
        default_factory=lambda: [
            "semantic",
            "multi_source",
            "statute",
            "case_law",
            "document",
            "cross_reference",
        ]
    )
    aa_dashboard_types: list[str] = field(
        default_factory=lambda: ["assistant", "research", "knowledge", "intelligence"]
    )
    aa_knowledge_bases: list[str] = field(
        default_factory=lambda: ["assistant", "research", "opinion", "authority", "reasoning"]
    )
    ei_analytics_kinds: list[str] = field(
        default_factory=lambda: [
            "case_success",
            "court_performance",
            "judge",
            "legal_cost",
            "contract",
            "compliance",
            "risk_trend",
        ]
    )
    ei_risk_score_types: list[str] = field(
        default_factory=lambda: ["enterprise", "department", "counterparty", "contract"]
    )
    ei_decision_kinds: list[str] = field(
        default_factory=lambda: [
            "executive",
            "priority_action",
            "strategy",
            "resource_allocation",
            "mitigation",
            "scenario",
        ]
    )
    ei_report_types: list[str] = field(
        default_factory=lambda: [
            "daily_briefing",
            "weekly_summary",
            "monthly_risk",
            "nl_report",
            "strategic_insight",
        ]
    )
    ei_alert_types: list[str] = field(
        default_factory=lambda: [
            "critical",
            "deadline",
            "compliance",
            "court",
            "contract",
            "regulatory",
        ]
    )
    ei_dashboard_types: list[str] = field(
        default_factory=lambda: ["executive", "risk", "forecast", "strategy", "operations"]
    )
    ei_knowledge_bases: list[str] = field(
        default_factory=lambda: ["executive", "risk", "forecast", "recommendation", "alert"]
    )


DEFAULT_CONFIG = LegalEnterpriseConfig()
