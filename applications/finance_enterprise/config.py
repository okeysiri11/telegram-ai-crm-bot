"""Finance Enterprise Platform — Sprint 18.0 Foundation (Bidex)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FinanceEnterpriseConfig:
    application_name: str = "Finance Enterprise Platform (Bidex)"
    application: str = "finance_enterprise"
    application_version: str = "5.1.0-enterprise"
    release_status: str = "Finance Enterprise Foundation"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v5.0.0-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/finance-enterprise/v1"
    internal_prefix: str = "/internal/finance-enterprise/v1"
    financial_registry: str = "1.0"
    general_ledger: str = "1.0"
    multi_currency: str = "1.0"
    financial_architecture: str = "1.0"
    knowledge: str = "1.0"
    analytics: str = "1.0"
    base_currency: str = "USD"
    account_types: list[str] = field(
        default_factory=lambda: ["asset", "liability", "equity", "revenue", "expense"]
    )
    entity_types: list[str] = field(
        default_factory=lambda: ["organization", "customer", "vendor", "cost_center", "other"]
    )
    finance_roles: list[str] = field(
        default_factory=lambda: [
            "cfo",
            "controller",
            "accountant",
            "treasury",
            "auditor",
            "analyst",
        ]
    )
    dashboard_types: list[str] = field(
        default_factory=lambda: ["overview", "accounts", "cash", "currency", "health"]
    )
    knowledge_bases: list[str] = field(
        default_factory=lambda: ["account", "ledger", "currency", "entity", "finance"]
    )


DEFAULT_CONFIG = FinanceEnterpriseConfig()
