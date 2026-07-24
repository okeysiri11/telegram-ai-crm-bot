"""Enterprise Onboarding constants — Sprint 22.9."""

from __future__ import annotations

WIZARD_STEPS = (
    "company_registration",
    "industry_selection",
    "branches",
    "working_hours",
    "currency_taxes",
    "roles",
    "readiness_check",
)

IMPORT_ENTITIES = (
    "clients",
    "employees",
    "services",
    "products",
    "inventory",
    "certificates",
    "memberships",
    "bonuses",
    "schedules",
)

IMPORT_SOURCES = ("excel", "csv", "api", "future_connectors")

GO_LIVE_ITEMS = (
    "import_completed",
    "employees_ready",
    "calendar_configured",
    "services_verified",
    "communications_working",
    "payments_configured",
    "ai_activated",
    "backup_completed",
)

KPI_TARGETS = {
    "salon_setup_under_30_min": True,
    "validated_import": True,
    "minimize_manual_steps": True,
    "standardized_go_live": True,
}

INTEGRATION_TARGETS = (
    "beauty_os",
    "commerce_core",
    "communications_hub",
    "ai_marketing_os",
    "ai_business_advisor",
    "product_intelligence",
    "crm",
    "calendar",
    "security_center",
)

PRINCIPLES = (
    "wizard_driven_setup",
    "validated_data_import",
    "ai_assists_never_mutates",
    "reuse_enterprise_services",
    "go_live_only_after_checklist",
    "no_duplicated_business_logic",
)

INDUSTRIES = ("beauty", "cafe", "retail", "medical", "construction", "other")
