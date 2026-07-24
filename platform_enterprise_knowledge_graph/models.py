"""Enterprise Knowledge Graph constants — Sprint 24.2."""

from __future__ import annotations

ENTITY_TYPES = (
    "company",
    "branch",
    "employee",
    "customer",
    "supplier",
    "product",
    "service",
    "appointment",
    "order",
    "invoice",
    "payment",
    "workflow",
    "ai_agent",
    "campaign",
    "document",
    "asset",
    "event",
    "task",
    "project",
    "contract",
    "conversation",
)

RELATION_TYPES = (
    "owns",
    "belongs_to",
    "created_by",
    "assigned_to",
    "managed_by",
    "purchased",
    "visited",
    "related_to",
    "depends_on",
    "generated_by_ai",
    "approved_by_owner",
    "part_of",
    "follows",
    "references",
)

CONTEXT_SOURCES = (
    "crm",
    "commerce",
    "marketing",
    "workflow",
    "communications",
    "product_intelligence",
    "operations_center",
)

KPI_TARGETS = {
    "context_in_milliseconds": True,
    "fewer_repeat_queries": True,
    "higher_recommendation_quality": True,
    "unified_semantic_memory": True,
}

INTEGRATION_TARGETS = (
    "unified_knowledge",
    "knowledge_platform",
    "product_intelligence",
    "ai_business_advisor",
    "ai_marketing_os",
    "commerce_core",
    "communications_hub",
    "workflow_intelligence",
    "enterprise_ai_orchestrator",
    "operations_center",
    "beauty_os",
    "client_portal",
)

PRINCIPLES = (
    "single_semantic_space",
    "long_term_platform_memory",
    "ai_uses_shared_context",
    "owner_controls_ai_data_use",
    "learn_from_confirmed_outcomes",
    "no_duplicated_business_logic",
)
