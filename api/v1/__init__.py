# API v1 scaffold — route stubs without business logic.
# Not wired into production startup by default (safe night task).
# Register via: from api.v1 import register_api_v1_routes

from __future__ import annotations

from aiohttp import web


async def _stub(request: web.Request) -> web.Response:
    resource = request.match_info.get("resource") or request.path
    return web.json_response(
        {
            "ok": True,
            "scaffold": True,
            "message": "API v1 endpoint reserved — business logic not migrated yet",
            "path": request.path,
            "resource": resource,
        },
        status=501,
    )


async def health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "api": "v1", "scaffold": True})


def register_api_v1_routes(app: web.Application) -> None:
    """Attach /api/v1 scaffold routes. Safe to call — does not alter legacy /v1 or /api."""
    app.router.add_get("/api/v1", health)
    app.router.add_get("/api/v1/", health)
    for path in (
        "/api/v1/leads",
        "/api/v1/clients",
        "/api/v1/managers",
        "/api/v1/inventory",
        "/api/v1/analytics",
    ):
        app.router.add_get(path, _stub)
        app.router.add_post(path, _stub)
