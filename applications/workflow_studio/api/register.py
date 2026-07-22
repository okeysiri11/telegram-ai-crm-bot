"""Register Workflow Studio routes (Sprint 12.2)."""

from __future__ import annotations

from aiohttp import web

from applications.workflow_studio.api import handlers
from applications.workflow_studio.api.middleware import auth_middleware
from applications.workflow_studio.config import DEFAULT_CONFIG


def register_workflow_studio_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_get(f"{prefix}/workflows", handlers.workflows_handler)
    app.router.add_post(f"{prefix}/workflows", handlers.workflows_handler)
    app.router.add_get(f"{prefix}/workflows/{{workflow_id}}/canvas", handlers.canvas_handler)
    app.router.add_post(f"{prefix}/workflows/{{workflow_id}}/canvas", handlers.canvas_handler)
    app.router.add_post(f"{prefix}/execute", handlers.execute_handler)
    app.router.add_post(f"{prefix}/ai-builder", handlers.ai_builder_handler)
    app.router.add_get(f"{prefix}/templates", handlers.templates_handler)
    app.router.add_post(f"{prefix}/templates", handlers.templates_handler)
    app.router.add_post(f"{prefix}/enterprise", handlers.enterprise_handler)
    app.router.add_get(f"{prefix}/monitoring", handlers.monitoring_handler)
    app.router.add_post(f"{prefix}/monitoring", handlers.monitoring_handler)
