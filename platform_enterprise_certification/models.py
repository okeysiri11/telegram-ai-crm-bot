"""Certification constants — Sprint 25.7."""

from __future__ import annotations

CERT_FIELDS = (
    "certification_id",
    "platform_version",
    "build_number",
    "release_candidate",
    "certification_date",
    "result",
    "approved_by",
    "status",
)

QUALITY_GATES = (
    "unit_tests",
    "integration_tests",
    "smoke_tests",
    "regression_tests",
    "performance_tests",
    "chaos_tests",
    "security_verification",
    "migration_verification",
    "production_readiness",
)

ARCHITECTURE_TARGETS = (
    "enterprise_core",
    "ai_orchestrator",
    "enterprise_hub",
    "workflow_engine",
    "knowledge_graph",
    "event_bus",
    "marketplace",
    "ai_provider_hub",
    "monitoring_platform",
    "notification_platform",
)

DOCUMENTATION_ARTIFACTS = (
    "api_documentation",
    "architecture_documentation",
    "module_documentation",
    "deployment_guide",
    "administrator_guide",
    "user_guide",
    "release_notes",
    "change_log",
)

RELEASE_ARTIFACTS = (
    "release_package",
    "docker_images",
    "configuration_package",
    "environment_templates",
    "deployment_manifest",
    "version_metadata",
)

READINESS_DIMENSIONS = (
    "functional",
    "security",
    "performance",
    "infrastructure",
    "documentation",
    "deployment",
)

DASHBOARD_SECTIONS = (
    "overall_readiness",
    "quality_gates",
    "test_results",
    "security_status",
    "performance_status",
    "deployment_status",
    "documentation",
    "release_candidate",
    "final_certification",
)

REPORT_KINDS = (
    "certification",
    "executive_summary",
    "release",
    "deployment",
    "quality",
    "architecture",
    "compliance",
)

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "security_verification",
    "migration",
    "production_readiness",
    "observability",
    "performance_testing",
    "chaos_engineering",
    "test_infrastructure",
)

KPI_TARGETS = {
    "unified_certification_process": True,
    "automatic_quality_gates": True,
    "release_builder": True,
    "readiness_analyzer": True,
    "certification_dashboard": True,
    "auto_release_package": True,
    "full_release_history": True,
    "block_release_on_critical": True,
    "no_duplicated_erl_logic": True,
}

PRINCIPLES = (
    "enterprise_ready_status",
    "block_release_on_failed_gates",
    "additive_to_erl_epd_eqa",
    "integrates_security_migration_production_chaos_perf",
    "no_duplicated_business_logic",
    "phase3_web_platform_ready",
)

STAGE_25_COMPLETE = (
    "enterprise_test_infrastructure",
    "performance_platform",
    "chaos_engineering",
    "migration_disaster_recovery",
    "security_verification",
    "production_readiness",
    "enterprise_certification",
)
