"""Learning Engine constants — Sprint 24.8."""

from __future__ import annotations

KNOWLEDGE_TYPES = (
    "pattern",
    "best_practice",
    "failure_mode",
    "success_case",
    "ux_insight",
    "feature_request",
    "complaint",
    "refusal_reason",
)

VERIFICATION_STATUSES = (
    "pending",
    "awaiting_owner",
    "approved",
    "rejected",
    "policy_trusted",
)

FEEDBACK_CLASSES = (
    "suggestion",
    "error",
    "ux_issue",
    "wish",
    "new_feature",
    "complaint",
    "success_case",
    "refusal_reason",
)

COLLECTOR_SOURCES = (
    "crm",
    "erp",
    "marketing_os",
    "commerce",
    "communications",
    "workflow",
    "operations_center",
    "product_intelligence",
    "ai_business_advisor",
)

OWNER_ACTIONS = ("approve", "reject", "policy_trust")

INTEGRATION_TARGETS = (
    "enterprise_ai_orchestrator",
    "strategy_intelligence",
    "product_intelligence",
    "predictive_intelligence",
    "workflow_intelligence",
    "enterprise_knowledge_graph",
    "enterprise_digital_twin",
    "simulation_lab",
    "operations_center",
    "ai_marketing_os",
    "beauty_os",
    "commerce_core",
)

PRODUCT_EVOLUTION_PIPELINE = (
    "product_intelligence",
    "roadmap_generator",
    "backlog",
    "owner_approval",
    "development_pipeline",
)

AI_SAFETY = (
    "no_self_modify_algorithms",
    "no_delete_knowledge",
    "no_spread_unconfirmed",
    "no_learn_from_unconfirmed_errors",
)

KPI_TARGETS = {
    "unified_learning_engine": True,
    "confirmed_learning_only": True,
    "cross_industry_experience": True,
    "recommendation_quality_improves": True,
    "auto_product_backlog": True,
    "controlled_ai_evolution": True,
}

PRINCIPLES = (
    "confirmed_data_only",
    "owner_or_trust_policy",
    "anonymized_cross_tenant",
    "no_pii_between_tenants",
    "no_autonomous_algorithm_change",
    "no_duplicated_business_logic",
)
