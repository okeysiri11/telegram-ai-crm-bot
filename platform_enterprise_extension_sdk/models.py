"""Extension SDK constants — Sprint 25.0."""

from __future__ import annotations

EXTENSION_TYPES = (
    "industry_module",
    "ai_agent",
    "workflow",
    "dashboard",
    "ai_skill",
    "integration",
    "ui_component",
    "automation_pack",
)

LIFECYCLE_STATUSES = (
    "draft",
    "testing",
    "verified",
    "published",
    "installed",
    "updated",
    "deprecated",
    "archived",
)

PERMISSION_SCOPES = (
    "crm",
    "erp",
    "finance",
    "marketing",
    "calendar",
    "ai",
    "documents",
    "knowledge_graph",
    "workflow",
    "notifications",
    "commerce",
)

MARKETPLACE_CATEGORIES = (
    "industry_solutions",
    "ai_skills",
    "templates",
    "integrations",
    "ui_packs",
    "workflow_packs",
    "dashboard_packs",
)

VERIFICATION_CHECKS = (
    "security",
    "api",
    "compatibility",
    "automated_tests",
    "digital_signature",
)

INTEGRATION_TARGETS = (
    "enterprise_ai_orchestrator",
    "ai_provider_hub",
    "workflow_intelligence",
    "enterprise_knowledge_graph",
    "learning_engine",
    "strategy_intelligence",
    "ai_marketing_os",
    "beauty_os",
    "commerce_core",
    "communications_hub",
    "operations_center",
)

KPI_TARGETS = {
    "unified_sdk": True,
    "marketplace_foundation": True,
    "safe_extension_system": True,
    "independent_industry_modules": True,
    "lifecycle_management": True,
    "digital_signature": True,
    "centralized_permissions": True,
    "no_core_modification": True,
}

PRINCIPLES = (
    "sdk_and_public_api_only",
    "no_direct_core_access",
    "no_core_modification",
    "owner_or_admin_permissions",
    "signed_and_verified_before_publish",
    "safe_load_install_rollback",
    "no_duplicated_business_logic",
)
