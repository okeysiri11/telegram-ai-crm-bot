"""API middleware for Agro Enterprise."""

from __future__ import annotations

from aiohttp import web


def json_response(data, *, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


@web.middleware
async def auth_middleware(request: web.Request, handler):
    request["principal"] = request.headers.get("X-Principal")
    return await handler(request)
