"""Enterprise Operations Center constants — Sprint 23.0."""

from __future__ import annotations

COMPANY_STAGES = ("onboarding", "pilot", "production")

FEEDBACK_ROLES = ("owner", "admin", "master", "client")

MONITOR_TARGETS = (
    "api",
    "queues",
    "background_jobs",
    "ai_services",
    "external_integrations",
    "databases",
    "cache",
    "file_storage",
)

TENANT_HEALTH_DIMS = (
    "crm",
    "ai",
    "communications_hub",
    "commerce",
    "marketing",
)

OWNER_ACTIONS = (
    "launch_company",
    "promote_to_production",
    "approve_global_change",
    "approve_release",
    "approve_mass_update",
    "approve_ai_recommendation",
)

KPI_TARGETS = {
    "platform_uptime": True,
    "operation_speed": True,
    "user_activity": True,
    "pilot_success": True,
    "customer_satisfaction": True,
    "improvements_shipped": True,
    "incident_resolution_speed": True,
}

INTEGRATION_TARGETS = (
    "product_intelligence",
    "ai_business_advisor",
    "ai_marketing_os",
    "communications_hub",
    "commerce_core",
    "beauty_os",
    "client_portal",
    "security_center",
    "monitoring_system",
    "release_manager",
)

PRINCIPLES = (
    "ops_over_dev_mode",
    "pilot_companies_managed_centrally",
    "feedback_flows_to_epi",
    "ai_recommends_owner_approves",
    "expert_board_then_owner",
    "no_duplicated_business_logic",
)
