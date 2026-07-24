"""Release platform constants — Sprint 21.8."""

from __future__ import annotations

CERTIFICATION_DOMAINS = (
    "architecture",
    "security",
    "performance",
    "quality",
    "documentation",
    "api",
    "data_contracts",
    "ai_platform",
    "enterprise_hub",
)

READINESS_CHECKS = (
    "production_configuration",
    "secrets",
    "environment_variables",
    "network",
    "dns",
    "ssl_tls",
    "monitoring",
    "logging",
)

DEPLOYMENT_PACKAGES = (
    "docker_compose",
    "kubernetes",
    "helm",
    "production_images",
    "installers",
    "upgrade_packages",
)

MIGRATION_KINDS = (
    "database",
    "configuration",
    "dto",
    "event_contracts",
    "version_compatibility",
)

VALIDATION_SCENARIOS = (
    "cold_start",
    "upgrade",
    "scaling",
    "failover",
    "recovery",
    "security",
    "soak",
)

MONITORING_STACK = (
    "prometheus",
    "grafana",
    "opentelemetry",
    "centralized_logging",
    "alerts",
    "health_checks",
    "sla_dashboard",
)

RPO_SECONDS = 300
RTO_SECONDS = 900

LTS_VERSION = "6.0.0"
LTS_LABEL = "Enterprise Core v6.0 LTS"

INTEGRATION_TARGETS = (
    "performance_platform",
    "quality_assurance",
    "security_hardening",
    "documentation_platform",
    "observability",
    "kubernetes",
    "enterprise_hub",
)

PRODUCTION_STATUSES = (
    "Enterprise Core v6.0 (LTS)",
    "Production Ready",
    "Enterprise Certified",
    "Security Validated",
    "Performance Certified",
    "Documentation Complete",
    "API Standardized",
    "Data Contracts Standardized",
    "Quality Assured",
    "AI Platform Certified",
)
