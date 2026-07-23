"""Register Finance Enterprise routes (Sprint 18.0)."""

from __future__ import annotations

from aiohttp import web

from applications.finance_enterprise.api import handlers
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
