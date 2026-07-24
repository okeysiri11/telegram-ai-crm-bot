"""Autonomous Optimization constants — Sprint 24.6."""

from __future__ import annotations

CATEGORIES = (
    "process",
    "resource",
    "revenue",
    "cost",
    "customer_experience",
)

OWNER_STATUSES = (
    "proposed",
    "council_review",
    "awaiting_owner",
    "approved",
    "rejected",
    "modified",
    "implemented",
    "verified",
)

COUNCIL_ROLES = (
    "product",
    "business",
    "architecture",
    "finance",
    "security",
    "marketing",
    "ux",
    "qa",
)

OWNER_ACTIONS = ("approve", "reject", "modify")

INTEGRATION_TARGETS = (
    "enterprise_digital_twin",
    "predictive_intelligence",
    "simulation_lab",
    "enterprise_knowledge_graph",
    "workflow_intelligence",
    "product_intelligence",
    "operations_center",
    "enterprise_ai_orchestrator",
)

KPI_TARGETS = {
    "continuous_improvement_search": True,
    "ranked_opportunities": True,
    "measurable_economic_effect": True,
    "learn_only_confirmed": True,
    "no_autonomous_critical_changes": True,
}

PRINCIPLES = (
    "propose_never_auto_deploy",
    "council_then_owner",
    "ranked_by_value_and_risk",
    "verify_after_implementation",
    "learn_from_confirmed_only",
    "no_duplicated_business_logic",
)
