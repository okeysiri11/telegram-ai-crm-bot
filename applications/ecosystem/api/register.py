"""Register Unified AI Ecosystem routes (Sprint 12.0)."""

from __future__ import annotations

from aiohttp import web

from applications.ecosystem.api import handlers
from applications.ecosystem.api.middleware import auth_middleware
from applications.ecosystem.config import DEFAULT_CONFIG


def register_ai_ecosystem_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_get(f"{prefix}/agents", handlers.agents_handler)
    app.router.add_post(f"{prefix}/agents", handlers.agents_handler)
    app.router.add_post(f"{prefix}/memory", handlers.memory_handler)
    app.router.add_get(f"{prefix}/exchange", handlers.exchange_handler)
    app.router.add_post(f"{prefix}/exchange", handlers.exchange_handler)
    app.router.add_post(f"{prefix}/auth", handlers.auth_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/search", handlers.search_handler)
    app.router.add_get(f"{prefix}/settings", handlers.settings_handler)
    app.router.add_post(f"{prefix}/settings", handlers.settings_handler)
    app.router.add_post(f"{prefix}/notifications", handlers.notifications_handler)
    app.router.add_get(f"{prefix}/events", handlers.events_handler)
    app.router.add_post(f"{prefix}/events", handlers.events_handler)
    app.router.add_get(f"{prefix}/gateway", handlers.gateway_handler)
    app.router.add_post(f"{prefix}/gateway", handlers.gateway_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/analytics", handlers.analytics_handler)
