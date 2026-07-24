"""Predictive Intelligence constants — Sprint 24.3."""

from __future__ import annotations

FORECAST_DOMAINS = (
    "revenue",
    "profit",
    "staff_load",
    "demand",
    "sales",
    "expenses",
    "cashflow",
)

CUSTOMER_PREDICTIONS = (
    "revisit_probability",
    "churn_probability",
    "purchase_probability",
    "expected_ltv",
    "promo_sensitivity",
    "loyalty_level",
)

MARKETING_PREDICTIONS = (
    "campaign_effectiveness",
    "conversion",
    "roi",
    "best_channel",
    "best_send_time",
    "expected_client_growth",
)

OPERATIONS_PREDICTIONS = (
    "staff_overload",
    "material_shortage",
    "procurement_need",
    "branch_overload",
    "open_slots",
    "idle_time",
)

RISK_TYPES = (
    "financial",
    "operational",
    "customer_loss",
    "process_failure",
    "security",
)

SCENARIO_KINDS = ("optimistic", "baseline", "conservative", "crisis")

INTEGRATION_TARGETS = (
    "crm",
    "commerce_core",
    "ai_marketing_os",
    "communications_hub",
    "workflow_intelligence",
    "enterprise_knowledge_graph",
    "operations_center",
    "product_intelligence",
)

KPI_TARGETS = {
    "forecast_all_core_domains": True,
    "unified_risk_scoring": True,
    "early_problem_detection": True,
    "proactive_owner_recommendations": True,
    "continuous_accuracy_improvement": True,
}

PRINCIPLES = (
    "single_prediction_layer",
    "explainable_forecasts",
    "scenarios_with_confidence",
    "learn_only_from_confirmed_actuals",
    "ai_recommends_never_acts",
    "owner_dashboard_only_actions",
    "no_duplicated_business_logic",
)
