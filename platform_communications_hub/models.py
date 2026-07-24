"""Communications Hub constants — Sprint 22.6."""

from __future__ import annotations

CHANNELS = (
    "sms",
    "email",
    "push",
    "telegram",
    "whatsapp",
    "viber",
    "voice_call",
)

CONNECTOR_CHANNELS = ("whatsapp", "viber")
FUTURE_CHANNELS = ("voice_call",)

AUTOMATION_SCENARIOS = (
    "new_appointment",
    "reschedule",
    "cancellation",
    "visit_confirmation",
    "post_visit_thanks",
    "rebook_invite",
    "birthday",
    "membership_ending",
    "open_slot",
    "marketing_promo",
)

INDUSTRIES = (
    "beauty",
    "cafe",
    "retail",
    "construction",
    "medical",
    "manufacturing",
    "crypto",
    "port",
)

INTEGRATION_TARGETS = (
    "beauty_os",
    "ai_marketing_os",
    "ai_business_advisor",
    "product_intelligence",
    "enterprise_crm",
    "enterprise_calendar",
    "notification_center",
    "communications",
)

PRINCIPLES = (
    "single_gateway_for_all_messages",
    "no_module_sends_independently",
    "ai_never_sends_alone",
    "owner_or_approved_automation_required",
    "industry_universal_api",
    "reuse_existing_comms_without_duplication",
)
