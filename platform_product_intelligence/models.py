"""Product Intelligence constants — Sprint 22.0."""

from __future__ import annotations

FEEDBACK_SOURCES = (
    "user_feedback",
    "support",
    "suggestion",
    "bug",
    "telemetry",
    "usage_analytics",
    "test_results",
    "ai_business_advisor",
    "ai_marketing",
    "internal_ai_agents",
)

EXPERT_ROLES = (
    "product",
    "technical",
    "ux",
    "business",
    "security",
    "architecture",
    "qa",
)

OWNER_DECISIONS = (
    "approve",
    "approve_with_changes",
    "return_for_revision",
    "need_more_research",
    "reject",
)

APPROVED_DECISIONS = ("approve", "approve_with_changes")

PIPELINE_ARTIFACTS = (
    "epic",
    "feature",
    "story",
    "sprint",
    "technical_tasks",
    "qa_tasks",
    "documentation_tasks",
)

PRINCIPLES = (
    "ai_never_modifies_system",
    "expert_analysis_required",
    "owner_final_decision",
    "measurable_expected_effect",
    "post_release_validation",
    "decision_history_retained",
)

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "event_platform",
    "quality_assurance",
    "ai_agents",
    "observability",
    "command_center",
    "workflow",
)
