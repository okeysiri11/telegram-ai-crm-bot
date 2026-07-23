"""Register Enterprise Hub routes (Sprint 19.0)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub.api import handlers
from applications.enterprise_hub.api.middleware import auth_middleware
from applications.enterprise_hub.config import DEFAULT_CONFIG


def register_enterprise_hub_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_post(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_get(f"{prefix}/integration", handlers.integration_handler)
    app.router.add_post(f"{prefix}/integration", handlers.integration_handler)
    app.router.add_get(f"{prefix}/identity", handlers.identity_handler)
    app.router.add_post(f"{prefix}/identity", handlers.identity_handler)
    app.router.add_get(f"{prefix}/configuration", handlers.configuration_handler)
    app.router.add_post(f"{prefix}/configuration", handlers.configuration_handler)
    app.router.add_get(f"{prefix}/events", handlers.events_handler)
    app.router.add_post(f"{prefix}/events", handlers.events_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)
