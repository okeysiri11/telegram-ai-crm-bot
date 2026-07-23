"""Enterprise Hub — Sprint 19.1 AI Orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnterpriseHubConfig:
    application_name: str = "Enterprise Integration Hub"
    application: str = "enterprise_hub"
    application_version: str = "5.3.1-enterprise"
    release_status: str = "AI Orchestrator"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v5.3.0-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/enterprise-hub/v1"
    orchestrator_api_prefix: str = "/api/enterprise-orch/v1"
    internal_prefix: str = "/internal/enterprise-hub/v1"
    enterprise_registry: str = "1.0"
    integration_layer: str = "1.0"
    enterprise_identity: str = "1.0"
    enterprise_configuration: str = "1.0"
    event_infrastructure: str = "1.0"
    orchestrator: str = "1.0"
    knowledge: str = "1.0"
    analytics: str = "1.0"
    known_platforms: list[str] = field(
        default_factory=lambda: [
            "platform_core",
            "ai_os",
            "enterprise",
            "automotive",
            "agro",
            "port",
            "crypto",
            "legal",
            "finance",
        ]
    )
    environment_types: list[str] = field(
        default_factory=lambda: ["development", "staging", "production", "sandbox"]
    )
    event_kinds: list[str] = field(
        default_factory=lambda: ["domain", "integration", "system", "audit"]
    )
    dashboard_types: list[str] = field(
        default_factory=lambda: [
            "overview",
            "platform_status",
            "integration_health",
            "connected_services",
            "environment_status",
        ]
    )
    knowledge_bases: list[str] = field(
        default_factory=lambda: [
            "platform",
            "integration",
            "service",
            "environment",
            "enterprise",
        ]
    )
    orch_workflow_kinds: list[str] = field(
        default_factory=lambda: ["sequential", "parallel", "conditional"]
    )
    orch_task_classes: list[str] = field(
        default_factory=lambda: [
            "operation",
            "settlement",
            "reporting",
            "compliance",
            "sync",
        ]
    )
    orch_template_kinds: list[str] = field(
        default_factory=lambda: ["sequential", "parallel", "conditional", "approval"]
    )
    orch_route_platforms: list[str] = field(
        default_factory=lambda: [
            "automotive",
            "agro",
            "port",
            "crypto",
            "legal",
            "finance",
        ]
    )
    orch_decision_types: list[str] = field(
        default_factory=lambda: [
            "execution_strategy",
            "platform_selection",
            "resource_optimization",
            "conflict_resolution",
            "recommendation",
            "execution_validation",
        ]
    )
    orch_explain_types: list[str] = field(
        default_factory=lambda: [
            "execution_reasoning",
            "decision_trace",
            "workflow_summary",
            "execution_confidence",
            "nl_explanation",
        ]
    )
    orch_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "orchestrator",
            "workflow",
            "execution",
            "platform_activity",
            "ai_decision",
        ]
    )
    orch_knowledge_bases: list[str] = field(
        default_factory=lambda: [
            "workflow",
            "execution",
            "task",
            "decision",
            "routing",
        ]
    )


DEFAULT_CONFIG = EnterpriseHubConfig()
