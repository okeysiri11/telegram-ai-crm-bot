# Visual Workflow Studio & AI Flow Builder — Sprint 12.2.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkflowStudioConfig:
    application_name: str = "Workflow Studio"
    application: str = "workflow_studio"
    application_version: str = "3.2.0-alpha"
    release_status: str = "Workflow Studio Alpha"
    platform_dependency: str = "AI Platform Core v3.0"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    marketplace_dependency: str = "AI Marketplace 3.1"
    api_version: str = "v1"
    api_prefix: str = "/api/workflow-studio/v1"
    internal_prefix: str = "/internal/workflow-studio/v1"
    visual_editor: str = "1.0"
    flow_engine: str = "1.0"
    ai_builder: str = "1.0"
    business_templates: str = "1.0"
    enterprise: str = "1.0"
    monitoring: str = "1.0"
    node_types: list[str] = field(
        default_factory=lambda: [
            "ai_agent",
            "tool",
            "connector",
            "database",
            "webhook",
            "api",
            "condition",
            "loop",
            "switch",
            "delay",
            "timer",
            "scheduler",
            "approval",
            "human_task",
            "notification",
            "file",
            "memory",
            "knowledge",
            "llm",
            "decision",
            "planning",
            "reasoning",
        ]
    )
    business_template_keys: list[str] = field(
        default_factory=lambda: [
            "crm",
            "erp",
            "accounting",
            "drone_mission",
            "drone_manufacturing",
            "construction",
            "auto_marketplace",
            "agro_marketplace",
            "legal",
            "finance",
            "hr",
            "customer_support",
            "sales_pipeline",
        ]
    )


DEFAULT_CONFIG = WorkflowStudioConfig()
