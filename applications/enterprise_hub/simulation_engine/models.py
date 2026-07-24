"""Simulation & Decision Intelligence models — Sprint 20.9."""

from __future__ import annotations

SCENARIO_DOMAINS = (
    "finance",
    "logistics",
    "manufacturing",
    "warehouse",
    "hr",
    "procurement",
    "construction",
    "maritime",
    "custom",
)

SCENARIO_KINDS = (
    "what_if",
    "profit_change",
    "demand_increase",
    "equipment_failure",
    "resource_cost_change",
)

DECISION_CRITERIA = ("profit", "cost", "risk", "time", "efficiency", "success_probability")
FORECAST_TARGETS = (
    "sales",
    "production_load",
    "cash_flow",
    "workforce_demand",
    "logistics",
    "inventory",
    "project_schedule",
    "maintenance",
)
RISK_KINDS = (
    "financial",
    "operational",
    "logistics",
    "manufacturing",
    "workforce",
    "project",
    "dependency",
)
SIM_STATUSES = ("draft", "scheduled", "running", "completed", "failed", "cancelled", "continuous")
SCHEDULE_MODES = ("manual", "scheduled", "event_bus", "continuous")
RECOMMENDATION_ACTIONS = (
    "increase_inventory",
    "reschedule_delivery",
    "redistribute_workforce",
    "change_production_schedule",
    "acquire_equipment",
)
INTEGRATION_TARGETS = (
    "digital_twin",
    "knowledge_platform",
    "data_fabric",
    "event_bus",
    "workflow",
    "ai_orchestrator",
    "business_rules",
)
