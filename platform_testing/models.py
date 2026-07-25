"""Test Infrastructure constants — Sprint 25.1."""

from __future__ import annotations

TEST_CATEGORIES = (
    "unit",
    "integration",
    "smoke",
    "regression",
    "e2e",
    "api",
    "performance",
    "security",
    "ai",
    "workflow",
    "migration",
    "chaos",
)

PIPELINE_STAGES = (
    "discovery",
    "validation",
    "preparation",
    "execution",
    "verification",
    "reporting",
    "analytics",
)

ENVIRONMENTS = (
    "development",
    "local",
    "docker",
    "ci",
    "staging",
    "production_mirror",
)

DATA_ENTITY_TYPES = (
    "users",
    "companies",
    "clients",
    "deals",
    "documents",
    "products",
    "warehouses",
    "payments",
    "ai_dialogs",
    "workflows",
    "notifications",
)

REPORT_FORMATS = ("html", "json", "xml", "console")

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "enterprise_ai_orchestrator",
    "workflow",
    "enterprise_knowledge_graph",
    "event_platform",
    "ai_provider_hub",
    "extension_sdk",
    "observability",
)

KPI_TARGETS = {
    "unified_test_registry": True,
    "unified_test_runner": True,
    "test_dashboard": True,
    "centralized_reports": True,
    "test_analytics": True,
    "ready_for_smoke_integration_regression": True,
    "no_duplicated_test_logic": True,
}

PRINCIPLES = (
    "single_test_center",
    "isolated_environments",
    "auto_generated_test_data",
    "pipeline_every_run",
    "centralized_reporting",
    "no_duplicated_test_logic",
)
