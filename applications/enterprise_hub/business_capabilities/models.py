"""Business Capability models — Sprint 20.11."""

from __future__ import annotations

MATURITY_LEVELS = (
    (1, "manual"),
    (2, "documented"),
    (3, "standardized"),
    (4, "automated"),
    (5, "ai_driven"),
)

CAPABILITY_DOMAINS = (
    "finance",
    "sales",
    "crm",
    "procurement",
    "logistics",
    "warehouse",
    "manufacturing",
    "construction",
    "maritime",
    "healthcare",
    "legal",
    "hr",
    "ai_operations",
    "custom",
)

CAPABILITY_STATUSES = ("draft", "active", "deprecated", "archived")

ADVISOR_ACTIONS = (
    "automate_capability",
    "deploy_ai",
    "merge_processes",
    "rebalance_load",
    "invest_max_roi",
)

INTEGRATION_TARGETS = (
    "digital_twin",
    "process_mining",
    "simulation_engine",
    "data_fabric",
    "workflow",
    "ai_orchestrator",
    "knowledge_platform",
    "command_center",
)
