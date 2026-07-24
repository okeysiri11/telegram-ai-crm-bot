"""Documentation platform constants — Sprint 21.6."""

from __future__ import annotations

DOC_CATEGORIES = (
    "architecture",
    "api",
    "modules",
    "ai",
    "security",
    "deployment",
    "operations",
    "sdk",
    "user_guides",
)

DOC_CHANNELS = ("release", "release_candidate", "lts", "development")

PUBLISH_FORMATS = ("html", "pdf", "markdown", "internal_portal", "developer_portal", "administrator_portal")

QUALITY_CHECKS = (
    "missing_sections",
    "broken_links",
    "stale_pages",
    "api_mismatch",
    "missing_examples",
    "completeness",
)

HUB_MODULES = (
    "orchestrator",
    "workflow",
    "ai_orchestrator",
    "event_platform",
    "data_fabric",
    "digital_twin",
    "process_mining",
    "business_capabilities",
    "command_center",
    "api_standardization",
    "data_contracts",
    "security_hardening",
    "quality_assurance",
)

INTEGRATION_TARGETS = (
    "openapi",
    "sdk",
    "developer_portal",
    "ci_cd",
    "quality_assurance",
    "enterprise_hub",
)
