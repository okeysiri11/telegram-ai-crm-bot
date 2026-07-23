"""Register Finance Enterprise routes (Sprint 18.0)."""

from __future__ import annotations

from aiohttp import web

from applications.finance_enterprise.api import handlers, pay_handlers
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
