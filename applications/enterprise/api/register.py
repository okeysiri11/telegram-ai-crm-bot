"""Register Enterprise Edition routes (Sprint 12.5)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise.api import handlers
from applications.enterprise.api.middleware import auth_middleware
from applications.enterprise.config import DEFAULT_CONFIG


def register_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/platform", handlers.platform_handler)
    app.router.add_post(f"{prefix}/platform", handlers.platform_handler)
    app.router.add_get(f"{prefix}/administration", handlers.administration_handler)
    app.router.add_post(f"{prefix}/administration", handlers.administration_handler)
    app.router.add_get(f"{prefix}/ai", handlers.ai_handler)
    app.router.add_post(f"{prefix}/ai", handlers.ai_handler)
    app.router.add_get(f"{prefix}/services", handlers.services_handler)
    app.router.add_post(f"{prefix}/services", handlers.services_handler)
    app.router.add_get(f"{prefix}/infrastructure", handlers.infrastructure_handler)
    app.router.add_post(f"{prefix}/infrastructure", handlers.infrastructure_handler)
    app.router.add_get(f"{prefix}/analytics", handlers.analytics_handler)
    app.router.add_post(f"{prefix}/analytics", handlers.analytics_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)
