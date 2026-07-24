"""Quality assurance constants — Sprint 21.5."""

from __future__ import annotations

UNIT_TARGETS = (
    "core_services",
    "ai_engine",
    "crm",
    "erp",
    "workflow",
    "security",
    "data_contracts",
    "enterprise_hub",
)

INTEGRATION_PAIRS = (
    ("api", "crm"),
    ("crm", "erp"),
    ("erp", "workflow"),
    ("workflow", "ai"),
    ("ai", "event_bus"),
    ("data_fabric", "analytics"),
    ("security", "all_services"),
)

E2E_SCENARIOS = (
    "register_organization",
    "create_user",
    "authorize",
    "create_deal",
    "start_workflow",
    "call_ai_agent",
    "generate_report",
    "complete_business_process",
)

CONTRACT_CHECKS = (
    "dto",
    "event_contracts",
    "api_contracts",
    "schema_registry",
    "version_compatibility",
)

AI_CHECKS = (
    "ai_orchestrator",
    "task_routing",
    "memory_engine",
    "knowledge_platform",
    "tool_calling",
    "fault_tolerance",
    "decision_correctness",
)

REGRESSION_AREAS = (
    "api",
    "workflow",
    "ai",
    "security",
    "integrations",
    "user_scenarios",
)

PERF_METRICS = (
    "api_latency_ms",
    "ai_throughput",
    "workflow_speed",
    "event_processing",
    "memory_usage_mb",
    "cpu_usage_pct",
)

QUALITY_METRICS = (
    "code_coverage",
    "mutation_score",
    "test_pass_rate",
    "build_success_rate",
    "defect_density",
    "mttd",
    "mttr",
)

MIN_COVERAGE = 0.90

INTEGRATION_TARGETS = (
    "ci_cd",
    "enterprise_hub",
    "api_standardization",
    "data_contracts",
    "security_hardening",
    "sdk",
)
