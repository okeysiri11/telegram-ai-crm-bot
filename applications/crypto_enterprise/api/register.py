"""Register Crypto Enterprise routes (Sprint 16.0)."""

from __future__ import annotations

from aiohttp import web

from applications.crypto_enterprise.api import handlers
from applications.crypto_enterprise.api.middleware import auth_middleware
from applications.crypto_enterprise.config import DEFAULT_CONFIG


def register_crypto_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/exchanges", handlers.exchanges_handler)
    app.router.add_post(f"{prefix}/exchanges", handlers.exchanges_handler)
    app.router.add_get(f"{prefix}/markets", handlers.markets_handler)
    app.router.add_post(f"{prefix}/markets", handlers.markets_handler)
    app.router.add_get(f"{prefix}/assets", handlers.assets_handler)
    app.router.add_post(f"{prefix}/assets", handlers.assets_handler)
    app.router.add_get(f"{prefix}/portfolio", handlers.portfolio_handler)
    app.router.add_post(f"{prefix}/portfolio", handlers.portfolio_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)
