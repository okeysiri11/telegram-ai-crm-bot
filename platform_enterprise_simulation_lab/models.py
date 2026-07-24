"""Simulation Lab constants — Sprint 24.4."""

from __future__ import annotations

SIMULATION_DOMAINS = (
    "finance",
    "sales",
    "marketing",
    "workforce",
    "schedule",
    "inventory",
    "branch_load",
    "ai_processes",
    "workflow",
)

WHAT_IF_QUESTIONS = (
    "increase_prices",
    "open_branch",
    "change_schedule",
    "increase_ad_budget",
    "hire_staff",
    "change_loyalty",
)

SCENARIO_KINDS = ("optimistic", "realistic", "conservative", "crisis")

IMPACT_DIMS = (
    "profit",
    "revenue",
    "staff_load",
    "customer_satisfaction",
    "marketing",
    "inventory",
    "cashflow",
    "risks",
)

INTEGRATION_TARGETS = (
    "enterprise_knowledge_graph",
    "predictive_intelligence",
    "workflow_intelligence",
    "product_intelligence",
    "commerce_core",
    "ai_marketing_os",
    "operations_center",
    "enterprise_ai_orchestrator",
)

KPI_TARGETS = {
    "model_any_business_decision": True,
    "compare_strategies": True,
    "forecast_before_rollout": True,
    "reduce_bad_decisions": True,
    "accumulate_successful_scenarios": True,
}

PRINCIPLES = (
    "simulate_before_deploy",
    "safe_sandbox_only",
    "council_debate_then_owner",
    "ai_never_rolls_out_alone",
    "compare_options_explicitly",
    "no_duplicated_business_logic",
)
