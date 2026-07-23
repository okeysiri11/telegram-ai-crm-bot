"""Register Port Enterprise routes (Sprint 15.0)."""

from __future__ import annotations

from aiohttp import web

from applications.port_enterprise.api import handlers
from applications.port_enterprise.api.middleware import auth_middleware
from applications.port_enterprise.config import DEFAULT_CONFIG


def register_port_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/ports", handlers.ports_handler)
    app.router.add_post(f"{prefix}/ports", handlers.ports_handler)
    app.router.add_get(f"{prefix}/terminals", handlers.terminals_handler)
    app.router.add_post(f"{prefix}/terminals", handlers.terminals_handler)
    app.router.add_get(f"{prefix}/cargo", handlers.cargo_handler)
    app.router.add_post(f"{prefix}/cargo", handlers.cargo_handler)
    app.router.add_get(f"{prefix}/shipping", handlers.shipping_handler)
    app.router.add_post(f"{prefix}/shipping", handlers.shipping_handler)
    app.router.add_get(f"{prefix}/fleet", handlers.fleet_handler)
    app.router.add_post(f"{prefix}/fleet", handlers.fleet_handler)
    app.router.add_get(f"{prefix}/operations", handlers.operations_handler)
    app.router.add_post(f"{prefix}/operations", handlers.operations_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)
