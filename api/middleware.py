# Public API Gateway v1 — authentication middleware.

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from aiohttp import web

from services.pg_api_gateway_engine import (
    ApiAuthenticationError,
    ApiAuthContext,
    ApiGatewayEngineV1,
    ApiPermissionError,
    ApiRateLimitError,
)

Handler = Callable[[web.Request], Awaitable[web.Response]]


def _request_id(request: web.Request) -> str:
    return request.headers.get("X-Request-ID") or str(uuid.uuid4())


def _client_ip(request: web.Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.transport:
        peer = request.transport.get_extra_info("peername")
        if peer:
            return peer[0]
    return None


async def _error_response(
    request: web.Request,
    *,
    status: int,
    error: str,
    ctx: ApiAuthContext | None,
    started: float,
    message: str | None = None,
) -> web.Response:
    rid = _request_id(request)
    duration_ms = int((time.monotonic() - started) * 1000)
    await ApiGatewayEngineV1.log_request(
        ctx=ctx,
        method=request.method,
        path=request.path,
        status_code=status,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        request_id=rid,
        duration_ms=duration_ms,
        error_message=message or error,
    )
    return web.json_response(
        {"error": error, "request_id": rid, "api_version": "v1"},
        status=status,
    )


def require_api_auth(handler: Handler) -> Handler:
    @wraps(handler)
    async def wrapper(request: web.Request) -> web.Response:
        started = time.monotonic()
        ctx: ApiAuthContext | None = None
        try:
            ctx = await ApiGatewayEngineV1.authenticate_request(
                authorization=request.headers.get("Authorization"),
                api_key_header=request.headers.get("X-API-Key"),
            )
            await ApiGatewayEngineV1.check_rate_limit(
                ctx,
                method=request.method,
                path=request.path,
            )
            ApiGatewayEngineV1.check_permission(ctx, request.method, request.path)
            request["api_context"] = ctx
            request["request_id"] = _request_id(request)

            response = await handler(request)

            duration_ms = int((time.monotonic() - started) * 1000)
            await ApiGatewayEngineV1.log_request(
                ctx=ctx,
                method=request.method,
                path=request.path,
                status_code=response.status,
                ip_address=_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
                request_id=request["request_id"],
                duration_ms=duration_ms,
            )
            return response
        except ApiAuthenticationError as exc:
            return await _error_response(
                request,
                status=401,
                error="authentication_failed",
                ctx=ctx,
                started=started,
                message=str(exc),
            )
        except ApiPermissionError as exc:
            return await _error_response(
                request,
                status=403,
                error="permission_denied",
                ctx=ctx,
                started=started,
                message=str(exc),
            )
        except ApiRateLimitError as exc:
            return await _error_response(
                request,
                status=429,
                error="rate_limit_exceeded",
                ctx=ctx,
                started=started,
                message=str(exc),
            )
        except web.HTTPException:
            raise
        except Exception as exc:
            return await _error_response(
                request,
                status=500,
                error="internal_error",
                ctx=ctx,
                started=started,
                message=str(exc),
            )

    return wrapper


def api_context(request: web.Request) -> ApiAuthContext:
    return request["api_context"]
