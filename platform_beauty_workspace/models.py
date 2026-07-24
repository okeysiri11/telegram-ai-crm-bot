"""Beauty Workspace constants — Sprint 22.3."""

from __future__ import annotations

SCHEDULE_VIEWS = ("day", "week", "month")

STATUS_COLORS = {
    "booked": "#3B82F6",
    "confirmed": "#10B981",
    "waiting": "#F59E0B",
    "rescheduled": "#8B5CF6",
    "cancelled": "#EF4444",
    "completed": "#6B7280",
    "rebooked": "#06B6D4",
}

RECEPTION_ACTIONS = (
    "new_appointment",
    "new_customer",
    "reschedule",
    "cancel",
    "check_in",
    "complete_visit",
    "sell_product",
    "sell_certificate",
    "sell_membership",
)

QUICK_ACTIONS = (
    "book_in_30s",
    "repeat_last_visit",
    "book_family",
    "add_multiple_services",
    "move_entire_appointment",
)

NOTIFICATION_KINDS = (
    "new_appointment",
    "cancellation",
    "reschedule",
    "client_late",
    "open_slot",
    "ai_recommendation",
    "system",
)

SEARCH_TARGETS = (
    "customers",
    "phones",
    "services",
    "employees",
    "certificates",
    "memberships",
    "appointments",
)

INTEGRATION_TARGETS = (
    "beauty_os",
    "enterprise_crm",
    "enterprise_calendar",
    "ai_business_advisor",
    "product_intelligence",
    "notification_center",
)

PRINCIPLES = (
    "first_screen_after_login",
    "min_clicks_daily_ops",
    "realtime_updates",
    "reuse_beauty_os",
    "ai_proposes_never_executes",
    "no_duplicated_business_logic",
)
