"""Workflow Intelligence constants — Sprint 24.1."""

from __future__ import annotations

DESIGNER_NODES = (
    "start",
    "end",
    "decision",
    "condition",
    "delay",
    "ai_decision",
    "human_approval",
    "api_call",
    "database",
    "notification",
    "payment",
    "crm",
    "calendar",
    "marketing",
    "commerce",
)

APPROVAL_KINDS = (
    "owner_approval",
    "manager_approval",
    "employee_approval",
    "ai_recommendation",
)

EXECUTION_POLICIES = (
    "automatic",
    "requires_manager",
    "requires_owner",
    "simulation_only",
    "ai_recommendation_only",
)

INDUSTRY_LIBRARY = (
    "beauty",
    "cafe",
    "retail",
    "construction",
    "manufacturing",
    "medical",
    "crypto",
    "port",
)

CROSS_MODULES = (
    "crm",
    "erp",
    "commerce",
    "marketing",
    "communications",
    "ai_business_advisor",
    "product_intelligence",
    "calendar",
    "documents",
    "finance",
    "warehouse",
    "analytics",
    "enterprise_ai_orchestrator",
    "workflow_engine",
)

KPI_TARGETS = {
    "success_rate_95pct": True,
    "visual_modeling": True,
    "scalability": True,
    "full_audit": True,
    "versioning": True,
}

PRINCIPLES = (
    "unify_workflow_and_ai_council",
    "ai_never_starts_critical_alone",
    "owner_decision_center_required",
    "visual_designer_first",
    "policy_gated_execution",
    "learn_optimize_propose_only",
    "no_duplicated_business_logic",
)
