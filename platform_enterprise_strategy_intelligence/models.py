"""Strategy Intelligence constants — Sprint 24.7."""

from __future__ import annotations

GOAL_TYPES = (
    "revenue_growth",
    "profit_growth",
    "scale",
    "open_branches",
    "cost_reduction",
    "efficiency",
    "customer_retention",
    "digital_transformation",
)

STRATEGY_STATUSES = (
    "draft",
    "council_review",
    "awaiting_owner",
    "approved",
    "rejected",
    "modified",
    "in_execution",
    "completed",
)

FORECAST_HORIZONS = ("quarter", "half_year", "year", "three_years", "five_years")

SCENARIO_TYPES = ("baseline", "aggressive_growth", "conservative", "crisis")

COUNCIL_ROLES = (
    "business",
    "finance",
    "marketing",
    "product",
    "architecture",
    "operations",
    "security",
    "legal",
    "analytics",
)

OWNER_ACTIONS = ("approve", "reject", "modify")

RISK_TYPES = (
    "market",
    "financial",
    "workforce",
    "technology",
    "operational",
)

INTEGRATION_TARGETS = (
    "enterprise_ai_orchestrator",
    "workflow_intelligence",
    "enterprise_knowledge_graph",
    "predictive_intelligence",
    "simulation_lab",
    "enterprise_digital_twin",
    "autonomous_optimization",
    "product_intelligence",
    "operations_center",
)

KPI_TARGETS = {
    "unified_strategic_planning": True,
    "measurable_goals": True,
    "execution_forecast": True,
    "risk_analysis": True,
    "ai_recommendations": True,
    "single_strategy_command_center": True,
    "owner_final_decision": True,
}

PRINCIPLES = (
    "propose_never_auto_decide",
    "council_then_owner",
    "scenario_based_planning",
    "measurable_kpis",
    "risk_aware",
    "no_duplicated_business_logic",
)
