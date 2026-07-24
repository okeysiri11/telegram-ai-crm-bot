"""Client Portal constants — Sprint 22.8."""

from __future__ import annotations

MOBILE_PLATFORMS = ("android", "ios", "pwa")

PUSH_KINDS = (
    "booking_confirmation",
    "reminder",
    "reschedule",
    "promo",
    "personal_offer",
    "salon_message",
)

KPI_TARGETS = {
    "booking_under_60s": True,
    "reduce_admin_load": True,
    "increase_rebooks": True,
    "loyalty_usage_growth": True,
    "campaign_conversion_growth": True,
}

INTEGRATION_TARGETS = (
    "beauty_os",
    "smart_booking",
    "beauty_client_journey",
    "commerce_core",
    "communications_hub",
    "ai_marketing_os",
    "ai_business_advisor",
)

PRINCIPLES = (
    "self_service_without_admin_calls",
    "reuse_enterprise_services",
    "mobile_first",
    "ai_recommends_never_acts",
    "secure_account_controls",
    "no_duplicated_business_logic",
)
