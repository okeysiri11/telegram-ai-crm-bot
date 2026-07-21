# Agro Marketplace API middleware — Ecosystem Identity authentication.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace.integrations.ecosystem_bridge import ecosystem_bridge


@web.middleware
async def auth_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return await handler(request)

    public_suffixes = (
        "/health",
        "/products",
        "/catalog/search",
        "/listings",
        "/categories",
        "/search/products",
        "/search/crops",
        "/search/harvests",
        "/search/warehouses",
        "/search/suppliers",
        "/search/semantic",
        "/ai/health",
        "/ai/agents",
        "/knowledge/search",
        "/knowledge/taxonomy",
        "/recommendations/products",
    )
    if request.method == "GET" and any(request.path.endswith(s) for s in public_suffixes):
        request["ecosystem_user"] = None
        return await handler(request)

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    user = ecosystem_bridge.validate_identity(token) if token else None
    if user is None and request.path.startswith("/internal/"):
        return error_response("Authentication required", status=401)
    request["ecosystem_user"] = user
    return await handler(request)


def json_response(data: object, *, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


def error_response(message: str, *, status: int = 400) -> web.Response:
    return web.json_response({"error": message}, status=status)
