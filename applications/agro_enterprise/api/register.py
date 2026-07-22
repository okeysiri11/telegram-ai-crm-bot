"""Register Agro Enterprise routes (Sprint 14.0)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise.api import handlers
from applications.agro_enterprise.api.middleware import auth_middleware
from applications.agro_enterprise.config import DEFAULT_CONFIG


def register_agro_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/marketplace", handlers.marketplace_handler)
    app.router.add_post(f"{prefix}/marketplace", handlers.marketplace_handler)
    app.router.add_get(f"{prefix}/farms", handlers.farms_handler)
    app.router.add_post(f"{prefix}/farms", handlers.farms_handler)
    app.router.add_get(f"{prefix}/crops", handlers.crops_handler)
    app.router.add_post(f"{prefix}/crops", handlers.crops_handler)
    app.router.add_get(f"{prefix}/crm", handlers.crm_handler)
    app.router.add_post(f"{prefix}/crm", handlers.crm_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
