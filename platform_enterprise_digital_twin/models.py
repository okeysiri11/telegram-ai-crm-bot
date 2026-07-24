"""Enterprise Digital Twin 2.0 constants — Sprint 24.5."""

from __future__ import annotations

SYNC_TARGETS = (
    "crm",
    "commerce",
    "marketing",
    "communications",
    "workflow",
    "enterprise_knowledge_graph",
    "predictive_intelligence",
    "simulation_lab",
    "operations_center",
)

LIVE_METRICS = (
    "customers",
    "active_appointments",
    "sales",
    "staff_load",
    "inventory",
    "campaigns",
    "finance",
    "ai_status",
    "services_status",
)

TIME_PRESETS = ("1h", "1d", "1w", "1m", "custom")

KPI_TARGETS = {
    "realtime_updates": True,
    "cross_module_sync": True,
    "full_transparency": True,
    "single_owner_monitoring_point": True,
}

PRINCIPLES = (
    "one_twin_per_company",
    "live_state_first",
    "changes_reflect_in_twin",
    "shared_source_for_pin_esl_eao",
    "owner_visibility",
    "no_duplicated_business_logic",
)
