"""Register AI OS routes (Sprint 12.4)."""

from __future__ import annotations

from aiohttp import web

from applications.ai_os.api import handlers
from applications.ai_os.api.middleware import auth_middleware
from applications.ai_os.config import DEFAULT_CONFIG


def register_ai_os_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/kernel", handlers.kernel_handler)
    app.router.add_post(f"{prefix}/kernel", handlers.kernel_handler)
    app.router.add_get(f"{prefix}/processes", handlers.process_handler)
    app.router.add_post(f"{prefix}/processes", handlers.process_handler)
    app.router.add_get(f"{prefix}/bus", handlers.bus_handler)
    app.router.add_post(f"{prefix}/bus", handlers.bus_handler)
    app.router.add_get(f"{prefix}/memory", handlers.memory_handler)
    app.router.add_post(f"{prefix}/memory", handlers.memory_handler)
    app.router.add_post(f"{prefix}/runtime", handlers.runtime_handler)
    app.router.add_get(f"{prefix}/communication", handlers.communication_handler)
    app.router.add_post(f"{prefix}/communication", handlers.communication_handler)
    app.router.add_get(f"{prefix}/enterprise", handlers.enterprise_handler)
    app.router.add_post(f"{prefix}/enterprise", handlers.enterprise_handler)
    app.router.add_get(f"{prefix}/observability", handlers.observability_handler)
    app.router.add_post(f"{prefix}/observability", handlers.observability_handler)
