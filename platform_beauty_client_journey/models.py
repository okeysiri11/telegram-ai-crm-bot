"""Beauty Client Journey constants — Sprint 22.4."""

from __future__ import annotations

BOOKING_CHANNELS = (
    "online",
    "administrator",
    "master",
    "rebook",
    "waitlist",
)

REMINDER_CHANNELS = (
    "sms",
    "email",
    "telegram",
    "push",
    "whatsapp",
)

REMINDER_KINDS = (
    "day_before",
    "hours_before",
    "after_visit",
    "rebook_invite",
)

LOYALTY_TRIGGERS = (
    "long_absence",
    "birthday",
    "membership_expired",
    "bonuses_expiring",
    "procedure_due",
)

JOURNEY_STAGES = (
    "first_contact",
    "acquisition_source",
    "first_booking",
    "visits",
    "cancellations",
    "reschedules",
    "purchases",
    "certificates",
    "memberships",
    "ai_recommendations",
    "loyalty_level",
)

KPI_TARGETS = {
    "booking_under_30s": True,
    "reduce_no_shows": True,
    "increase_revisits": True,
    "increase_avg_check": True,
    "increase_master_load": True,
}

INTEGRATION_TARGETS = (
    "beauty_os",
    "beauty_workspace",
    "enterprise_crm",
    "enterprise_calendar",
    "ai_business_advisor",
    "ai_marketing_os",
    "product_intelligence",
)

PRINCIPLES = (
    "full_client_lifecycle",
    "smart_booking_not_just_calendar",
    "reuse_enterprise_services",
    "ai_recommends_never_auto_acts",
    "owner_or_staff_confirmation_required",
)
