"""Enterprise Organization Brain — Sprint 27.2."""

from __future__ import annotations

VERSION = "9.4.0"
API_PREFIX = "/api/organization-brain/v1"
WEB_PATH = "src/web/organization-brain"
SPRINT = "27.2"
HUB = "enterprise_organization_brain"

ARCHITECTURE = (
    "organization_model",
    "executive_board",
    "department_orchestration",
    "business_decision_engine",
    "executive_meetings",
    "organization_knowledge",
    "executive_dashboard",
)

ORG_ENTITY_TYPES = (
    "companies",
    "holdings",
    "organizations",
    "departments",
    "teams",
    "employees",
    "contractors",
    "roles",
    "positions",
)

EXECUTIVE_BOARD = ("CEO", "COO", "CFO", "CTO", "CMO", "CHRO", "CLO")

DEPARTMENTS = (
    "Sales",
    "Marketing",
    "Finance",
    "HR",
    "Legal",
    "Manufacturing",
    "Logistics",
    "CRM",
    "ERP",
    "Analytics",
    "AI Department",
)

KNOWLEDGE_KINDS = (
    "structure",
    "regulations",
    "job_instructions",
    "policies",
    "kpi",
    "business_processes",
)

KPI_TARGETS = {
    "organization_model_ready": True,
    "executive_board_ready": True,
    "department_orchestration_ready": True,
    "decision_engine_ready": True,
    "executive_meetings_ready": True,
    "organization_knowledge_ready": True,
    "executive_dashboard_ready": True,
}

PRINCIPLES = (
    "digital_company_twin",
    "c_suite_ai_board",
    "department_first_orchestration",
    "kpi_driven_decisions",
    "protocolled_executive_meetings",
    "living_org_knowledge",
    "phase4_organization_brain",
)
