"""AI Business Advisor constants — Sprint 22.1."""

from __future__ import annotations

INDUSTRIES = (
    "beauty",
    "cafe",
    "construction",
    "retail",
    "manufacturing",
    "crypto",
    "healthcare",
    "finance",
    "legal",
    "generic",
)

HEALTH_DIMENSIONS = (
    "sales",
    "profit",
    "expenses",
    "customers",
    "repeat_visits",
    "staff_efficiency",
    "schedule_load",
    "service_usage",
    "marketing_campaigns",
)

OPPORTUNITY_KINDS = (
    "open_booking_slots",
    "revenue_decline",
    "customer_decline",
    "avg_check_decline",
    "repeat_visit_decline",
    "overloaded_staff",
    "underloaded_staff",
    "ineffective_services",
)

RECOMMENDATION_KINDS = (
    "launch_promotion",
    "adjust_prices",
    "offer_discount",
    "send_newsletter",
    "create_reels",
    "run_ad_campaign",
    "loyalty_program",
    "winback_customers",
)

FORECAST_KINDS = (
    "revenue",
    "profit",
    "staff_load",
    "bookings",
    "demand",
)

COMMERCIAL_ACTIONS = (
    "customers",
    "finance",
    "pricing",
    "staff",
    "marketing",
)

INTEGRATION_TARGETS = (
    "crm",
    "calendar",
    "finance",
    "warehouse",
    "ai_marketing_os",
    "product_intelligence",
)

OWNER_DECISIONS = ("approve", "reject", "defer")

PRINCIPLES = (
    "ai_analyzes_only",
    "ai_never_executes_commercial_actions",
    "owner_final_decision",
    "initiatives_flow_to_product_intelligence",
    "industry_universal",
)
