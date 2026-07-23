"""Enterprise Hub — Sprint 19.9 Enterprise Observability Platform."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnterpriseHubConfig:
    application_name: str = "Enterprise Integration Hub"
    application: str = "enterprise_hub"
    application_version: str = "5.3.9-enterprise"
    release_status: str = "Enterprise Observability"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v5.3.8-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/enterprise-hub/v1"
    orchestrator_api_prefix: str = "/api/enterprise-orch/v1"
    knowledge_graph_api_prefix: str = "/api/enterprise-kg/v1"
    ai_agents_api_prefix: str = "/api/enterprise-agents/v1"
    communications_api_prefix: str = "/api/enterprise-comms/v1"
    workflow_api_prefix: str = "/api/enterprise-workflow/v1"
    eip_api_prefix: str = "/api/enterprise-eip/v1"
    edp_api_prefix: str = "/api/enterprise-edp/v1"
    isam_api_prefix: str = "/api/enterprise-isam/v1"
    observability_api_prefix: str = "/api/enterprise-obs/v1"
    internal_prefix: str = "/internal/enterprise-hub/v1"
    enterprise_registry: str = "1.0"
    integration_layer: str = "1.0"
    enterprise_identity: str = "1.0"
    enterprise_configuration: str = "1.0"
    event_infrastructure: str = "1.0"
    orchestrator: str = "1.0"
    unified_knowledge: str = "1.0"
    ai_agents: str = "1.0"
    communications: str = "1.0"
    workflow: str = "1.0"
    eip: str = "1.0"
    edp: str = "1.0"
    isam: str = "1.0"
    observability: str = "1.0"
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
    kg_entity_types: list[str] = field(
        default_factory=lambda: [
            "person",
            "organization",
            "customer",
            "supplier",
            "partner",
            "asset",
            "vehicle",
            "contract",
            "invoice",
            "case",
            "crypto_asset",
        ]
    )
    kg_memory_types: list[str] = field(
        default_factory=lambda: [
            "long_term",
            "conversation",
            "business",
            "project",
            "decision",
            "workflow",
        ]
    )
    kg_semantic_ops: list[str] = field(
        default_factory=lambda: [
            "semantic_search",
            "entity_resolution",
            "duplicate_detection",
            "knowledge_inference",
            "relationship_discovery",
            "context_expansion",
            "similarity_analysis",
        ]
    )
    kg_context_types: list[str] = field(
        default_factory=lambda: [
            "automotive",
            "agro",
            "port",
            "crypto",
            "legal",
            "finance",
            "unified",
        ]
    )
    kg_ai_insight_types: list[str] = field(
        default_factory=lambda: [
            "recommendation",
            "context_reasoning",
            "cross_platform_correlation",
            "business_insight",
            "predictive",
            "nl_query",
        ]
    )
    kg_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "knowledge",
            "entity",
            "relationship",
            "ai_memory",
            "semantic",
        ]
    )
    kg_knowledge_bases: list[str] = field(
        default_factory=lambda: [
            "master",
            "ontology",
            "memory",
            "entity",
            "relationship",
        ]
    )
    aa_agent_types: list[str] = field(
        default_factory=lambda: [
            "automotive",
            "agro",
            "port",
            "crypto",
            "legal",
            "finance",
            "general",
        ]
    )
    aa_automation_kinds: list[str] = field(
        default_factory=lambda: [
            "scheduled",
            "event_driven",
            "rule_based",
            "approval",
        ]
    )
    aa_intel_types: list[str] = field(
        default_factory=lambda: [
            "task_optimization",
            "resource_optimization",
            "performance_recommendation",
            "knowledge_reuse",
            "context_decision",
        ]
    )
    aa_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "agents",
            "automation",
            "execution",
            "performance",
            "governance",
        ]
    )
    aa_knowledge_bases: list[str] = field(
        default_factory=lambda: [
            "agent_graph",
            "capability",
            "execution",
            "automation",
            "performance",
        ]
    )
    comm_channels: list[str] = field(
        default_factory=lambda: [
            "email",
            "telegram",
            "sms",
            "push",
            "websocket",
            "webhook",
            "corporate_chat",
            "future",
        ]
    )
    comm_priorities: list[str] = field(
        default_factory=lambda: ["critical", "high", "medium", "low", "silent"]
    )
    comm_queue_statuses: list[str] = field(
        default_factory=lambda: [
            "pending",
            "processing",
            "delivered",
            "failed",
            "retry",
            "expired",
        ]
    )
    comm_template_kinds: list[str] = field(
        default_factory=lambda: [
            "crm",
            "invoice",
            "lead",
            "task",
            "approval",
            "security",
            "ai_alert",
            "report",
        ]
    )
    comm_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "delivery",
            "queue",
            "channels",
            "audit",
            "analytics",
        ]
    )
    wf_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "performance",
            "approvals",
            "scheduler",
            "templates",
            "optimization",
        ]
    )
    wf_template_kinds: list[str] = field(
        default_factory=lambda: [
            "crm_lead_processing",
            "invoice_approval",
            "purchase_request",
            "employee_onboarding",
            "contract_approval",
            "ai_task_processing",
            "customer_support",
            "equipment_maintenance",
        ]
    )
    eip_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "monitoring",
            "registry",
            "sync",
            "connectors",
            "analytics",
        ]
    )
    edp_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "quality",
            "catalog",
            "governance",
            "lineage",
            "analytics",
        ]
    )
    isam_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "identity",
            "sessions",
            "access",
            "monitoring",
            "audit",
        ]
    )
    obs_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "platform",
            "infrastructure",
            "ai",
            "integrations",
            "business",
        ]
    )


DEFAULT_CONFIG = EnterpriseHubConfig()
