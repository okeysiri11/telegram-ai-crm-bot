"""HTTP security middleware — Sprint 30.0.

RequestId · Audit logging · Rate limiting · Secure headers · CSRF (cookie) · Input validation helpers.
Registered on the main aiohttp app without changing route contracts.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections import defaultdict, deque
from typing import Any

from aiohttp import web

logger = logging.getLogger(__name__)

_RATE_WINDOWS: dict[str, deque[float]] = defaultdict(deque)
_UNSAFE_QUERY = re.compile(r"(--|/\*|\*/|;|\bunion\b|\bdrop\b|\bexec\b)", re.I)


def _security_settings():
    try:
        from platform_configuration.configuration_center import configuration_center

        return configuration_center.settings.security
    except Exception:
        return None


def _client_ip(request: web.Request) -> str:
    """Resolve client IP.

    X-Forwarded-For is only trusted when ``TRUST_PROXY`` / ``security.trust_proxy``
    is enabled (Sprint 37.2). Otherwise peers can spoof rate-limit keys.
    """
    settings = _security_settings()
    trust_proxy = bool(getattr(settings, "trust_proxy", False)) if settings else False
    if trust_proxy:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    peer = request.transport.get_extra_info("peername") if request.transport else None
    return peer[0] if peer else "unknown"


@web.middleware
async def request_id_middleware(request: web.Request, handler):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request["request_id"] = request_id
    response = await handler(request)
    response.headers["X-Request-Id"] = request_id
    return response


@web.middleware
async def secure_headers_middleware(request: web.Request, handler):
    settings = _security_settings()
    response = await handler(request)
    if settings is None or settings.security_headers_enabled:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.headers.setdefault("X-XSS-Protection", "0")
        if not response.headers.get("Content-Security-Policy"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; img-src 'self' data: blob:; "
                "style-src 'self' 'unsafe-inline'; script-src 'self'; "
                "connect-src 'self'; frame-ancestors 'none'"
            )
    return response


@web.middleware
async def rate_limit_middleware(request: web.Request, handler):
    settings = _security_settings()
    if settings is not None and not settings.rate_limit_enabled:
        return await handler(request)

    limit = settings.rate_limit_per_minute if settings else 600
    key = f"{_client_ip(request)}:{request.path.split('?')[0]}"
    now = time.monotonic()
    window = _RATE_WINDOWS[key]
    while window and now - window[0] > 60.0:
        window.popleft()
    if len(window) >= limit:
        return web.json_response(
            {"success": False, "error": "rate_limit_exceeded", "retry_after_seconds": 60},
            status=429,
            headers={"Retry-After": "60"},
        )
    window.append(now)
    return await handler(request)


@web.middleware
async def audit_logging_middleware(request: web.Request, handler):
    started = time.monotonic()
    request_id = request.get("request_id") or request.headers.get("X-Request-Id", "")
    try:
        response = await handler(request)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if response.status >= 400:
            logger.info(
                "http_audit method=%s path=%s status=%s ms=%s request_id=%s ip=%s",
                request.method,
                request.path,
                response.status,
                elapsed_ms,
                request_id,
                _client_ip(request),
            )
        return response
    except web.HTTPException as exc:
        logger.info(
            "http_audit method=%s path=%s status=%s request_id=%s ip=%s",
            request.method,
            request.path,
            exc.status,
            request_id,
            _client_ip(request),
        )
        raise


@web.middleware
async def csrf_middleware(request: web.Request, handler):
    """CSRF check for cookie-authenticated mutating requests only.

    Bearer / API-key APIs are exempt (stateless). Disabled by default via config.
    """
    settings = _security_settings()
    if settings is None or not settings.csrf_protection_enabled:
        return await handler(request)
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return await handler(request)
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") or request.headers.get("X-API-Key"):
        return await handler(request)
    if "session" not in request.cookies and "csrftoken" not in request.cookies:
        return await handler(request)
    header_token = request.headers.get("X-CSRF-Token", "")
    cookie_token = request.cookies.get("csrftoken", "")
    if not header_token or header_token != cookie_token:
        return web.json_response({"success": False, "error": "csrf_failed"}, status=403)
    return await handler(request)


def validate_input_string(value: str, *, max_length: int = 4096, field: str = "input") -> str:
    if len(value) > max_length:
        raise web.HTTPBadRequest(text=f"{field} exceeds max length")
    if _UNSAFE_QUERY.search(value):
        raise web.HTTPBadRequest(text=f"{field} contains disallowed patterns")
    return value


def security_middleware_stack() -> list[Any]:
    """Ordered middleware list for create_app (outermost first in aiohttp append order)."""
    return [
        request_id_middleware,
        secure_headers_middleware,
        rate_limit_middleware,
        csrf_middleware,
        audit_logging_middleware,
    ]
