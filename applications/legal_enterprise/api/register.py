"""Register Legal Enterprise routes (Sprint 17.0)."""

from __future__ import annotations

from aiohttp import web

from applications.legal_enterprise.api import handlers
from applications.legal_enterprise.api.middleware import auth_middleware
from applications.legal_enterprise.config import DEFAULT_CONFIG


def register_legal_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_post(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_get(f"{prefix}/legislation", handlers.legislation_handler)
    app.router.add_post(f"{prefix}/legislation", handlers.legislation_handler)
    app.router.add_get(f"{prefix}/courts", handlers.courts_handler)
    app.router.add_post(f"{prefix}/courts", handlers.courts_handler)
    app.router.add_get(f"{prefix}/cases", handlers.cases_handler)
    app.router.add_post(f"{prefix}/cases", handlers.cases_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)
