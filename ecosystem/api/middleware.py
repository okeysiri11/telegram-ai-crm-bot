# Ecosystem API middleware.

from __future__ import annotations

from aiohttp import web

from ecosystem.engine import ecosystem_engine


@web.middleware
async def ecosystem_auth_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return await handler(request)

    public_suffixes = ("/health", "/auth/register", "/auth/login", "/auth/sso")
    if any(request.path.endswith(s) for s in public_suffixes):
        request["ecosystem_user"] = None
        return await handler(request)

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    user = ecosystem_engine.identity.validate_session(token) if token else None
    request["ecosystem_user"] = user
    return await handler(request)


def json_response(data: object, *, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


def error_response(message: str, *, status: int = 400) -> web.Response:
    return web.json_response({"error": message}, status=status)
