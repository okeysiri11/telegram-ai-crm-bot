# API middleware — authentication integration.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace.integrations.platform_bridge import platform_bridge


@web.middleware
async def auth_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return await handler(request)

    public_paths = ("/health", "/vehicles", "/search", "/dealers")
    path_suffix = request.path.rsplit("/", 1)[-1]
    if any(request.path.endswith(p) for p in public_paths) and request.method == "GET":
        request["principal"] = None
        return await handler(request)

    auth_header = request.headers.get("Authorization")
    principal = await platform_bridge.authenticate_request(auth_header)
    if principal is None and request.path.startswith("/internal/"):
        return error_response("Authentication required", status=401)
    request["principal"] = principal
    return await handler(request)


def json_response(data: object, *, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


def error_response(message: str, *, status: int = 400) -> web.Response:
    return web.json_response({"error": message}, status=status)
