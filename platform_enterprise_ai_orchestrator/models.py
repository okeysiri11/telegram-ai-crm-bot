"""Enterprise AI Orchestrator constants — Sprint 24.0 / v7.0."""

from __future__ import annotations

COUNCIL_ROLES = (
    "product",
    "technical",
    "architecture",
    "ux",
    "business",
    "finance",
    "marketing",
    "commerce",
    "security",
    "legal",
    "qa",
    "analytics",
)

OWNER_ACTIONS = (
    "approve",
    "approve_with_changes",
    "request_alternative",
    "send_for_review",
    "reject",
)

KPI_TARGETS = {
    "all_ai_via_orchestrator": True,
    "no_conflicting_ai_actions": True,
    "explained_decisions": True,
    "expert_council_review": True,
    "single_consolidated_brief": True,
}

INTEGRATION_TARGETS = (
    "product_intelligence",
    "ai_business_advisor",
    "ai_marketing_os",
    "operations_center",
    "commerce_core",
    "communications_hub",
    "beauty_os",
    "crm",
    "analytics",
    "security_center",
)

PRINCIPLES = (
    "single_orchestrator_for_all_ai",
    "specialized_expert_agents",
    "extensible_council_registry",
    "owner_final_authority",
    "ai_never_acts_alone",
    "explained_decisions_with_risks",
    "learn_only_from_confirmed_outcomes",
    "no_duplicated_business_logic",
)

DEFAULT_COMPETENCIES = {
    "product": ["roadmap", "feedback", "prioritization"],
    "technical": ["reliability", "performance", "integrations"],
    "architecture": ["modularity", "extensibility", "boundaries"],
    "ux": ["usability", "flows", "accessibility"],
    "business": ["strategy", "kpis", "operations"],
    "finance": ["unit_economics", "pricing", "risk"],
    "marketing": ["campaigns", "channels", "conversion"],
    "commerce": ["pos", "catalog", "loyalty"],
    "security": ["access", "compliance", "threats"],
    "legal": ["terms", "privacy", "liability"],
    "qa": ["quality", "regressions", "coverage"],
    "analytics": ["metrics", "forecasts", "anomalies"],
}
