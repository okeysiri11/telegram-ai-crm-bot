"""Enterprise Hub — Sprint 21.2 Enterprise API Standardization (Phase 2 Stabilization RC2)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnterpriseHubConfig:
    application_name: str = "Enterprise Integration Hub"
    application: str = "enterprise_hub"
    application_version: str = "6.0.0-rc2"
    release_status: str = "Enterprise API Standardization"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v5.4.12-enterprise"
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
    tenancy_api_prefix: str = "/api/enterprise-tenancy/v1"
    ai_orchestrator_api_prefix: str = "/api/enterprise-aop/v1"
    ai_tools_api_prefix: str = "/api/enterprise-ats/v1"
    knowledge_platform_api_prefix: str = "/api/enterprise-ekp/v1"
    aios_api_prefix: str = "/api/enterprise-aios/v1"
    event_platform_api_prefix: str = "/api/enterprise-evp/v1"
    developer_platform_api_prefix: str = "/api/enterprise-sdp/v1"
    data_fabric_api_prefix: str = "/api/enterprise-edf/v1"
    digital_twin_api_prefix: str = "/api/enterprise-edt/v1"
    simulation_engine_api_prefix: str = "/api/enterprise-esi/v1"
    process_mining_api_prefix: str = "/api/enterprise-epm/v1"
    business_capabilities_api_prefix: str = "/api/enterprise-ebc/v1"
    command_center_api_prefix: str = "/api/enterprise-ecc/v1"
    api_standardization_api_prefix: str = "/api/enterprise-eas/v1"
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
    tenancy: str = "1.0"
    ai_orchestrator: str = "1.0"
    ai_tools: str = "1.0"
    knowledge_platform: str = "1.0"
    aios: str = "1.0"
    event_platform: str = "1.0"
    developer_platform: str = "1.0"
    data_fabric: str = "1.0"
    digital_twin: str = "1.0"
    simulation_engine: str = "1.0"
    process_mining: str = "1.0"
    business_capabilities: str = "1.0"
    command_center: str = "1.0"
    api_standardization: str = "1.0"
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
    tenancy_license_tiers: list[str] = field(
        default_factory=lambda: [
            "free",
            "startup",
            "business",
            "enterprise",
            "government",
            "custom",
        ]
    )
    tenancy_workspace_kinds: list[str] = field(
        default_factory=lambda: ["crm", "erp", "finance", "ai", "custom", "documents"]
    )
    aop_strategies: list[str] = field(
        default_factory=lambda: ["sequential", "parallel", "voting", "delegation", "collaborative"]
    )
    ats_tool_domains: list[str] = field(
        default_factory=lambda: [
            "crm",
            "erp",
            "finance",
            "legal",
            "analytics",
            "files",
            "communication",
            "integrations",
            "browser",
            "terminal",
            "custom",
        ]
    )
    ekp_memory_tiers: list[str] = field(
        default_factory=lambda: [
            "short_term",
            "long_term",
            "project",
            "organization",
            "personal",
            "ai_shared",
        ]
    )
    aios_execution_modes: list[str] = field(
        default_factory=lambda: ["sequential", "parallel", "distributed", "recursive", "collaborative"]
    )
    evp_event_types: list[str] = field(
        default_factory=lambda: [
            "UserCreated",
            "LeadCreated",
            "ContractSigned",
            "PaymentReceived",
            "InvoiceApproved",
            "TaskCompleted",
            "ShipmentCreated",
            "AIJobFinished",
            "DocumentUpdated",
            "SecurityAlert",
        ]
    )
    sdp_plugin_kinds: list[str] = field(
        default_factory=lambda: ["module", "plugin", "ai_agent", "integration", "ui", "workflow", "custom"]
    )
    sdp_extension_points: list[str] = field(
        default_factory=lambda: [
            "menu",
            "ui",
            "ai_agents",
            "workflow",
            "reports",
            "dashboard",
            "forms",
            "events",
        ]
    )
    edf_asset_kinds: list[str] = field(
        default_factory=lambda: [
            "table",
            "document",
            "event",
            "vector_index",
            "file_store",
            "external",
            "ai_model",
        ]
    )
    edf_virtualization_modes: list[str] = field(
        default_factory=lambda: ["sql", "nosql", "graph", "vector", "object", "event_stream"]
    )
    edt_twin_types: list[str] = field(
        default_factory=lambda: [
            "organization",
            "department",
            "employee",
            "customer",
            "supplier",
            "project",
            "warehouse",
            "equipment",
            "vehicle",
            "vessel",
            "production",
            "asset",
            "ai_agent",
            "custom",
        ]
    )
    esi_scenario_domains: list[str] = field(
        default_factory=lambda: [
            "finance",
            "logistics",
            "manufacturing",
            "warehouse",
            "hr",
            "procurement",
            "construction",
            "maritime",
            "custom",
        ]
    )
    epm_event_sources: list[str] = field(
        default_factory=lambda: [
            "crm",
            "erp",
            "workflow",
            "event_bus",
            "ai_agents",
            "documents",
            "user_actions",
            "integrations",
        ]
    )


DEFAULT_CONFIG = EnterpriseHubConfig()
