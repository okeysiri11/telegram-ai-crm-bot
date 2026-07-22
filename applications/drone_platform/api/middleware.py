from __future__ import annotations

from aiohttp import web


@web.middleware
async def auth_middleware(request: web.Request, handler):
    # Foundation alpha: principal optional; bridges may enrich later.
    request["principal"] = None
    return await handler(request)


def json_response(data: object, *, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


def error_response(message: str, *, status: int = 400) -> web.Response:
    return web.json_response({"error": message}, status=status)
