# API v1 — frozen public contract entry point.

from __future__ import annotations

from aiohttp import web

from api.v1.public_router import register_public_api_v1_routes


async def _reserved_stub(request: web.Request) -> web.Response:
    from platform_api.responses import error_response

    return error_response(
        "Endpoint reserved for v1 migration",
        status=501,
    )


def register_api_v1_routes(app: web.Application) -> None:
    """Register all frozen /api/v1 routes and legacy compatibility aliases."""
    register_public_api_v1_routes(app)

    for path in (
        "/api/v1/leads",
        "/api/v1/clients",
        "/api/v1/managers",
        "/api/v1/inventory/crm",
        "/api/v1/analytics/crm",
    ):
        app.router.add_get(path, _reserved_stub)
        app.router.add_post(path, _reserved_stub)
