# Executive Command Center & Digital Twin — Sprint 12.3.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExecutiveCenterConfig:
    application_name: str = "Executive Command Center"
    application: str = "executive_center"
    application_version: str = "3.3.0-alpha"
    release_status: str = "Executive Center Alpha"
    platform_dependency: str = "AI Platform Core v3.0"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/executive/v1"
    internal_prefix: str = "/internal/executive/v1"
    executive_dashboard: str = "1.0"
    digital_twin: str = "1.0"
    system_monitoring: str = "1.0"
    executive_ai: str = "1.0"
    analytics: str = "1.0"
    visualization: str = "1.0"
    enterprise: str = "1.0"
    twin_types: list[str] = field(
        default_factory=lambda: [
            "application",
            "infrastructure",
            "business",
            "knowledge",
            "agent",
            "workflow",
            "drone",
            "marketplace",
        ]
    )
    dashboard_types: list[str] = field(
        default_factory=lambda: [
            "global",
            "company",
            "project",
            "department",
            "finance",
            "operations",
            "ai",
        ]
    )


DEFAULT_CONFIG = ExecutiveCenterConfig()
