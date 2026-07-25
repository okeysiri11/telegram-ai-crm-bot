"""Enterprise Platform Release Candidate — Sprint 26.8 / RC1."""

from __future__ import annotations

VERSION = "9.1.0-rc1"
API_PREFIX = "/api/release/v1"
RELEASE_CODE = "RC1"
SPRINT = "26.8"
WEB_PATH = "src/web/release"

INTEGRATION_MODULES = (
    "enterprise_web",
    "authentication",
    "workspace",
    "navigation",
    "enterprise_command_center",
    "dashboard",
    "analytics",
    "crm",
    "erp",
    "finance",
    "marketplace",
    "knowledge",
    "workflow_engine",
    "automation_engine",
    "notification_center",
    "ai_hub",
    "ai_orchestrator",
    "ai_agents",
    "reasoning",
    "memory",
    "knowledge_graph",
    "predictive_intelligence",
    "simulation_lab",
    "digital_twin",
    "learning_engine",
    "provider_hub",
    "security",
    "testing",
    "monitoring",
    "observability",
    "chaos",
    "performance",
    "release",
)

ARCHITECTURE = (
    "platform_integration_auditor",
    "application_registry_scanner",
    "routes_auditor",
    "security_reviewer",
    "performance_reviewer",
    "documentation_reviewer",
    "platform_health_report",
    "release_dashboard",
    "final_validation_gate",
)

KPI_TARGETS = {
    "platform_integrated": True,
    "release_candidate_ready": True,
    "health_report_ready": True,
    "documentation_verified": True,
    "security_reviewed": True,
    "performance_reviewed": True,
    "routes_audited": True,
    "registry_scanned": True,
}

PRINCIPLES = (
    "single_unified_platform",
    "release_candidate_discipline",
    "full_integration_verification",
    "health_first_release",
    "zero_critical_blockers",
    "phase3_release_candidate",
)

READINESS_WEIGHTS = {
    "integration": 0.25,
    "applications": 0.15,
    "routes": 0.10,
    "security": 0.20,
    "performance": 0.10,
    "documentation": 0.10,
    "tests": 0.10,
}
