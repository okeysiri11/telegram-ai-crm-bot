"""Finance Enterprise Platform — Sprint 18.5 Financial Reporting & BI (Bidex)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FinanceEnterpriseConfig:
    application_name: str = "Finance Enterprise Platform (Bidex)"
    application: str = "finance_enterprise"
    application_version: str = "5.1.5-enterprise"
    release_status: str = "Financial Reporting & BI"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v5.1.4-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/finance-enterprise/v1"
    payments_api_prefix: str = "/api/finance-pay/v1"
    billing_api_prefix: str = "/api/finance-bil/v1"
    treasury_api_prefix: str = "/api/finance-tr/v1"
    digital_assets_api_prefix: str = "/api/finance-da/v1"
    reporting_api_prefix: str = "/api/finance-rpt/v1"
    internal_prefix: str = "/internal/finance-enterprise/v1"
    financial_registry: str = "1.0"
    general_ledger: str = "1.0"
    multi_currency: str = "1.0"
    financial_architecture: str = "1.0"
    payments: str = "1.0"
    billing: str = "1.0"
    treasury: str = "1.0"
    digital_assets: str = "1.0"
    reporting: str = "1.0"
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
    pay_wallet_types: list[str] = field(
        default_factory=lambda: ["enterprise", "customer", "vendor", "multi_currency"]
    )
    pay_payment_types: list[str] = field(
        default_factory=lambda: [
            "internal",
            "incoming",
            "outgoing",
            "scheduled",
            "recurring",
            "bulk",
        ]
    )
    pay_payment_statuses: list[str] = field(
        default_factory=lambda: [
            "pending",
            "scheduled",
            "authorized",
            "approved",
            "rejected",
            "completed",
            "failed",
            "retrying",
            "cancelled",
        ]
    )
    pay_dashboard_types: list[str] = field(
        default_factory=lambda: ["payments", "wallets", "banking", "cash"]
    )
    pay_knowledge_bases: list[str] = field(
        default_factory=lambda: ["payment", "wallet", "bank", "cash", "transaction"]
    )
    bil_invoice_types: list[str] = field(
        default_factory=lambda: ["standard", "proforma", "recurring"]
    )
    bil_ai_insight_types: list[str] = field(
        default_factory=lambda: [
            "late_payment",
            "collection_recommendation",
            "cash_flow_risk",
            "invoice_anomaly",
            "revenue_forecast",
            "nl_summary",
        ]
    )
    bil_dashboard_types: list[str] = field(
        default_factory=lambda: ["invoice", "receivables", "payables", "tax", "cashflow"]
    )
    bil_knowledge_bases: list[str] = field(
        default_factory=lambda: ["invoice", "receivable", "payable", "tax", "cashflow"]
    )
    tr_budget_types: list[str] = field(
        default_factory=lambda: ["department", "project", "cost_center"]
    )
    tr_plan_types: list[str] = field(
        default_factory=lambda: [
            "revenue",
            "expense",
            "capex",
            "investment",
            "working_capital",
        ]
    )
    tr_forecast_kinds: list[str] = field(
        default_factory=lambda: ["cash_flow", "revenue", "expense", "liquidity"]
    )
    tr_variance_types: list[str] = field(
        default_factory=lambda: [
            "budget_vs_actual",
            "revenue",
            "expense",
            "cash_flow",
            "department",
        ]
    )
    tr_ai_insight_types: list[str] = field(
        default_factory=lambda: [
            "budget_deviation",
            "liquidity_risk",
            "forecast_optimization",
            "financial_anomaly",
            "capital_allocation",
            "nl_summary",
        ]
    )
    tr_dashboard_types: list[str] = field(
        default_factory=lambda: ["treasury", "budget", "forecast", "liquidity", "planning"]
    )
    tr_knowledge_bases: list[str] = field(
        default_factory=lambda: ["treasury", "budget", "forecast", "liquidity", "planning"]
    )
    da_networks: list[str] = field(
        default_factory=lambda: [
            "bitcoin",
            "ethereum",
            "tron",
            "bnb",
            "polygon",
            "solana",
            "evm",
        ]
    )
    da_wallet_types: list[str] = field(
        default_factory=lambda: ["hot", "cold", "multisig", "hd"]
    )
    da_operation_types: list[str] = field(
        default_factory=lambda: [
            "deposit",
            "withdrawal",
            "internal_transfer",
            "otc_settlement",
            "cross_wallet",
            "rebalance",
        ]
    )
    da_ai_insight_types: list[str] = field(
        default_factory=lambda: [
            "portfolio_risk",
            "wallet_risk",
            "market_exposure",
            "treasury_optimization",
            "liquidity_recommendation",
            "nl_report",
        ]
    )
    da_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "digital_assets",
            "treasury",
            "portfolio",
            "wallets",
            "exchange",
        ]
    )
    da_knowledge_bases: list[str] = field(
        default_factory=lambda: [
            "digital_asset",
            "wallet",
            "blockchain",
            "exchange",
            "treasury",
        ]
    )
    rpt_statement_types: list[str] = field(
        default_factory=lambda: [
            "balance_sheet",
            "profit_loss",
            "cash_flow",
            "trial_balance",
            "general_ledger",
            "equity",
        ]
    )
    rpt_management_types: list[str] = field(
        default_factory=lambda: [
            "department",
            "project_profitability",
            "cost_center",
            "business_unit",
            "budget_vs_actual",
            "executive_summary",
        ]
    )
    rpt_kpi_types: list[str] = field(
        default_factory=lambda: ["margin", "revenue", "expense", "liquidity", "efficiency"]
    )
    rpt_analytic_types: list[str] = field(
        default_factory=lambda: [
            "revenue",
            "expense",
            "margin",
            "profitability",
            "trend",
            "variance",
        ]
    )
    rpt_consolidation_types: list[str] = field(
        default_factory=lambda: [
            "multi_company",
            "intercompany_elimination",
            "consolidated_statements",
            "group_performance",
            "cross_platform",
        ]
    )
    rpt_forecast_kinds: list[str] = field(
        default_factory=lambda: ["revenue", "profit", "cash_flow", "liquidity"]
    )
    rpt_ai_insight_types: list[str] = field(
        default_factory=lambda: [
            "financial_health",
            "profitability_recommendation",
            "cost_optimization",
            "revenue_growth",
            "anomaly",
            "nl_report",
            "predictive",
        ]
    )
    rpt_dashboard_types: list[str] = field(
        default_factory=lambda: [
            "executive",
            "kpi",
            "profitability",
            "forecast",
            "enterprise_bi",
        ]
    )
    rpt_knowledge_bases: list[str] = field(
        default_factory=lambda: ["reporting", "kpi", "report", "forecast", "analytics"]
    )


DEFAULT_CONFIG = FinanceEnterpriseConfig()
