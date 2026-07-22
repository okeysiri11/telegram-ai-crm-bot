"""Register Executive Center routes (Sprint 12.3)."""

from __future__ import annotations

from aiohttp import web

from applications.executive_center.api import handlers
from applications.executive_center.api.middleware import auth_middleware
from applications.executive_center.config import DEFAULT_CONFIG


def register_executive_center_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/twins", handlers.twins_handler)
    app.router.add_post(f"{prefix}/twins", handlers.twins_handler)
    app.router.add_get(f"{prefix}/monitoring", handlers.monitoring_handler)
    app.router.add_post(f"{prefix}/monitoring", handlers.monitoring_handler)
    app.router.add_post(f"{prefix}/ai", handlers.ai_handler)
    app.router.add_get(f"{prefix}/analytics", handlers.analytics_handler)
    app.router.add_post(f"{prefix}/analytics", handlers.analytics_handler)
    app.router.add_get(f"{prefix}/visualization", handlers.visualization_handler)
    app.router.add_get(f"{prefix}/enterprise", handlers.enterprise_handler)
    app.router.add_post(f"{prefix}/enterprise", handlers.enterprise_handler)
