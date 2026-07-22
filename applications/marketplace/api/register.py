"""Register Marketplace routes (Sprint 12.1)."""

from __future__ import annotations

from aiohttp import web

from applications.marketplace.api import handlers
from applications.marketplace.api.middleware import auth_middleware
from applications.marketplace.config import DEFAULT_CONFIG


def register_marketplace_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_get(f"{prefix}/packages", handlers.packages_handler)
    app.router.add_post(f"{prefix}/packages", handlers.packages_handler)
    app.router.add_get(f"{prefix}/installations", handlers.installations_handler)
    app.router.add_get(f"{prefix}/agents", handlers.agents_handler)
    app.router.add_post(f"{prefix}/agents", handlers.agents_handler)
    app.router.add_get(f"{prefix}/workflows", handlers.workflows_handler)
    app.router.add_post(f"{prefix}/workflows", handlers.workflows_handler)
    app.router.add_get(f"{prefix}/connectors", handlers.connectors_handler)
    app.router.add_post(f"{prefix}/connectors", handlers.connectors_handler)
    app.router.add_post(f"{prefix}/security", handlers.security_handler)
    app.router.add_get(f"{prefix}/portal", handlers.portal_handler)
    app.router.add_post(f"{prefix}/portal", handlers.portal_handler)
    app.router.add_get(f"{prefix}/enterprise", handlers.enterprise_handler)
    app.router.add_post(f"{prefix}/enterprise", handlers.enterprise_handler)
