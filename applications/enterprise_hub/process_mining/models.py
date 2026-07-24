"""Process Mining models — Sprint 20.10."""

from __future__ import annotations

EVENT_SOURCES = (
    "crm",
    "erp",
    "workflow",
    "event_bus",
    "ai_agents",
    "documents",
    "user_actions",
    "integrations",
)

PROCESS_STATUSES = ("discovered", "conformed", "optimized", "archived")
VIOLATION_KINDS = ("skipped_step", "bypass", "sla_breach", "unordered", "extra_step")
BOTTLENECK_KINDS = ("delay", "overload", "idle", "rework", "cycle", "resource_wait")
ROOT_CAUSES = (
    "staff_shortage",
    "department_overload",
    "integration_error",
    "human_factor",
    "missing_materials",
    "supplier_delay",
)
OPTIMIZATION_ACTIONS = (
    "remove_step",
    "merge_approvals",
    "automate_checks",
    "reorder_steps",
    "rebalance_load",
    "deploy_ai_agent",
)
INTEGRATION_TARGETS = (
    "digital_twin",
    "simulation_engine",
    "workflow",
    "event_bus",
    "data_fabric",
    "knowledge_platform",
    "command_center",
)

# Canonical happy path for order-to-cash style processes
DEFAULT_REFERENCE_STEPS = (
    "create_request",
    "validate",
    "approve",
    "pay",
    "ship",
    "close",
)
