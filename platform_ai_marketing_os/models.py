"""AI Marketing OS constants — Sprint 22.5."""

from __future__ import annotations

CREATIVE_KINDS = (
    "image",
    "banner",
    "ad_layout",
    "stories",
    "reels",
    "shorts",
    "video",
    "texts",
    "ad_copy",
)

CONTENT_KINDS = (
    "ad_text",
    "post",
    "reels_script",
    "stories",
    "email",
    "sms",
    "push",
    "telegram",
)

CAMPAIGN_KINDS = (
    "discount",
    "promotion",
    "happy_hours",
    "winback",
    "new_service",
    "branch_opening",
    "special_offer",
)

APPROVAL_ACTIONS = ("approve", "edit", "reject", "schedule")

OPPORTUNITY_SIGNALS = (
    "open_hours",
    "underloaded_masters",
    "revenue_decline",
    "revisit_decline",
    "service_underuse",
)

INTEGRATION_TARGETS = (
    "beauty_os",
    "beauty_workspace",
    "beauty_client_journey",
    "ai_business_advisor",
    "product_intelligence",
    "notification_center",
    "enterprise_calendar",
    "enterprise_crm",
)

PRINCIPLES = (
    "ai_never_publishes_alone",
    "owner_approval_required",
    "daily_business_aware_marketing",
    "reuse_beauty_and_enterprise_services",
    "no_duplicated_business_logic",
    "results_feed_product_intelligence",
)
