"""Beauty OS constants — Sprint 22.2."""

from __future__ import annotations

INDUSTRY = "beauty"

FUTURE_INDUSTRIES = (
    "cafe",
    "medical",
    "construction",
    "retail",
    "manufacturing",
)

APPOINTMENT_STATUSES = (
    "booked",
    "confirmed",
    "rescheduled",
    "waiting",
    "cancelled",
    "completed",
    "rebooked",
)

RESOURCE_KINDS = ("room", "chair", "equipment", "device")

ENTERPRISE_DEPENDENCIES = (
    "enterprise_crm",
    "enterprise_calendar",
    "enterprise_finance",
    "ai_business_advisor",
    "product_intelligence",
)

PRINCIPLES = (
    "industry_overlay_not_core_fork",
    "reuse_enterprise_services",
    "no_duplicated_business_logic",
    "extensible_for_future_industries",
    "pilot_industry_for_ecosystem",
)
