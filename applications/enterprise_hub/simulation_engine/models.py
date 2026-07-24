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
SIM_STATUSES = ("draft", "scheduled", "running", "completed", "failed", "cancelled")
