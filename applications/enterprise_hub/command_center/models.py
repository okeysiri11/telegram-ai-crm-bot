"""Command Center models — Sprint 20.12."""

from __future__ import annotations

DASHBOARD_KINDS = (
    "executive",
    "operations",
    "finance",
    "logistics",
    "manufacturing",
    "construction",
    "maritime",
    "healthcare",
    "security",
    "ai",
    "custom",
)

WIDGET_KINDS = (
    "kpi",
    "charts",
    "maps",
    "timeline",
    "alerts",
    "ai_summary",
    "recommendations",
)

ALERT_SEVERITIES = ("info", "warning", "critical")
ALERT_KINDS = (
    "critical_event",
    "sla_breach",
    "financial_risk",
    "cyber_threat",
    "equipment_downtime",
    "process_deviation",
    "ai_recommendation",
)

ACTION_KINDS = (
    "start_workflow",
    "approve",
    "assign_task",
    "manage_ai_agent",
    "run_simulation",
    "replay_scenario",
    "manage_incident",
)

MAP_ENTITY_KINDS = (
    "department",
    "facility",
    "warehouse",
    "production",
    "equipment",
    "vessel",
    "transport",
    "construction_site",
    "healthcare_facility",
    "ai_component",
)

INTEGRATION_TARGETS = (
    "digital_twin",
    "simulation_engine",
    "process_mining",
    "business_capabilities",
    "workflow",
    "ai_orchestrator",
    "data_fabric",
    "knowledge_platform",
    "event_bus",
    "security",
    "identity",
    "marketplace",
    "sdk",
)

HEALTH_DIMENSIONS = (
    "performance",
    "financial_stability",
    "resource_utilization",
    "process_quality",
    "integration_health",
    "service_availability",
    "user_activity",
)
