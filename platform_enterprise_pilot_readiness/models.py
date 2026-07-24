"""Pilot Readiness constants — Sprint 23.1."""

from __future__ import annotations

AUDITED_SURFACES = (
    "beauty_workspace",
    "client_portal",
    "commerce",
    "marketing",
    "communications",
    "ai_business_advisor",
    "product_intelligence",
)

CORE_WORKFLOWS = (
    "client_booking",
    "service_sale",
    "product_sale",
    "certificate_issue",
    "campaign_create",
    "company_registration",
)

PILOT_CHECKLIST_ITEMS = (
    "services_ok",
    "ai_active",
    "communications_ok",
    "backups_enabled",
    "monitoring_active",
    "security_configured",
    "roles_configured",
    "licenses_active",
)

FEEDBACK_KINDS = ("review", "idea", "error", "rating")

KPI_TARGETS = {
    "core_flows_under_60s": True,
    "no_critical_errors": True,
    "self_serve_onboarding": True,
    "auto_feedback_collection": True,
}

INTEGRATION_TARGETS = (
    "beauty_workspace",
    "client_portal",
    "commerce_core",
    "ai_marketing_os",
    "communications_hub",
    "ai_business_advisor",
    "product_intelligence",
    "operations_center",
    "onboarding",
)

PRINCIPLES = (
    "polish_existing_not_new_modules",
    "shorten_core_workflows",
    "empty_states_and_first_launch",
    "ai_coaches_never_forces",
    "feedback_to_epi",
    "pilot_access_only_after_checklist",
    "no_duplicated_business_logic",
)
