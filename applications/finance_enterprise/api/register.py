"""Register Finance Enterprise routes (Sprint 18.0)."""

from __future__ import annotations

from aiohttp import web

from applications.finance_enterprise.api import bil_handlers, handlers, pay_handlers
from applications.finance_enterprise.api.middleware import auth_middleware
from applications.finance_enterprise.config import DEFAULT_CONFIG


def register_finance_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_post(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_get(f"{prefix}/ledger", handlers.ledger_handler)
    app.router.add_post(f"{prefix}/ledger", handlers.ledger_handler)
    app.router.add_get(f"{prefix}/currency", handlers.currency_handler)
    app.router.add_post(f"{prefix}/currency", handlers.currency_handler)
    app.router.add_get(f"{prefix}/architecture", handlers.architecture_handler)
    app.router.add_post(f"{prefix}/architecture", handlers.architecture_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)

    # Sprint 18.1 — Payments Platform (additive; prior routes unchanged)
    pay = DEFAULT_CONFIG.payments_api_prefix
    app.router.add_get(f"{pay}/health", pay_handlers.pay_health_handler)
    app.router.add_post(f"{pay}/bootstrap", pay_handlers.pay_bootstrap_handler)
    app.router.add_get(f"{pay}/banking", pay_handlers.pay_banking_handler)
    app.router.add_post(f"{pay}/banking", pay_handlers.pay_banking_handler)
    app.router.add_get(f"{pay}/wallets", pay_handlers.pay_wallets_handler)
    app.router.add_post(f"{pay}/wallets", pay_handlers.pay_wallets_handler)
    app.router.add_get(f"{pay}/payments", pay_handlers.pay_payments_handler)
    app.router.add_post(f"{pay}/payments", pay_handlers.pay_payments_handler)
    app.router.add_get(f"{pay}/cash", pay_handlers.pay_cash_handler)
    app.router.add_post(f"{pay}/cash", pay_handlers.pay_cash_handler)
    app.router.add_get(f"{pay}/processing", pay_handlers.pay_processing_handler)
    app.router.add_post(f"{pay}/processing", pay_handlers.pay_processing_handler)
    app.router.add_get(f"{pay}/controls", pay_handlers.pay_controls_handler)
    app.router.add_post(f"{pay}/controls", pay_handlers.pay_controls_handler)
    app.router.add_get(f"{pay}/dashboard", pay_handlers.pay_dashboard_handler)
    app.router.add_post(f"{pay}/dashboard", pay_handlers.pay_dashboard_handler)
    app.router.add_get(f"{pay}/knowledge", pay_handlers.pay_knowledge_handler)
    app.router.add_post(f"{pay}/knowledge", pay_handlers.pay_knowledge_handler)

    # Sprint 18.2 — Billing Platform (additive; prior routes unchanged)
    bil = DEFAULT_CONFIG.billing_api_prefix
    app.router.add_get(f"{bil}/health", bil_handlers.bil_health_handler)
    app.router.add_post(f"{bil}/bootstrap", bil_handlers.bil_bootstrap_handler)
    app.router.add_get(f"{bil}/invoices", bil_handlers.bil_invoices_handler)
    app.router.add_post(f"{bil}/invoices", bil_handlers.bil_invoices_handler)
    app.router.add_get(f"{bil}/quotations", bil_handlers.bil_quotations_handler)
    app.router.add_post(f"{bil}/quotations", bil_handlers.bil_quotations_handler)
    app.router.add_get(f"{bil}/receivables", bil_handlers.bil_receivables_handler)
    app.router.add_post(f"{bil}/receivables", bil_handlers.bil_receivables_handler)
    app.router.add_get(f"{bil}/payables", bil_handlers.bil_payables_handler)
    app.router.add_post(f"{bil}/payables", bil_handlers.bil_payables_handler)
    app.router.add_get(f"{bil}/tax", bil_handlers.bil_tax_handler)
    app.router.add_post(f"{bil}/tax", bil_handlers.bil_tax_handler)
    app.router.add_get(f"{bil}/cashflow", bil_handlers.bil_cashflow_handler)
    app.router.add_post(f"{bil}/cashflow", bil_handlers.bil_cashflow_handler)
    app.router.add_get(f"{bil}/ai", bil_handlers.bil_ai_handler)
    app.router.add_post(f"{bil}/ai", bil_handlers.bil_ai_handler)
    app.router.add_get(f"{bil}/dashboard", bil_handlers.bil_dashboard_handler)
    app.router.add_post(f"{bil}/dashboard", bil_handlers.bil_dashboard_handler)
    app.router.add_get(f"{bil}/knowledge", bil_handlers.bil_knowledge_handler)
    app.router.add_post(f"{bil}/knowledge", bil_handlers.bil_knowledge_handler)
