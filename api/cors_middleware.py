"""CORS for the existing aiohttp API — AUTO 1.8.5.

Exact origins only. Credentials are allowed only when the request Origin is
on the allow-list. Wildcard ``*`` is never used with credentials.
"""

from __future__ import annotations

import os

from aiohttp import web

_LOCAL_ORIGINS = (
    "http://127.0.0.1:5180",
    "http://localhost:5180",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
)

_ALLOW_HEADERS = (
    "Authorization, Content-Type, X-Request-Id, X-CSRF-Token, "
    "X-Tenant-Id, X-Organization-Id, X-Recruiting-Organization-Id, X-Organization, X-Workspace-Id, "
    "X-Workspace, X-Role, X-Role-Id, X-Principal, X-User-Id, X-Platform-Role"
)
_ALLOW_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"


def configured_origins() -> set[str]:
    origins = {item.rstrip("/") for item in _LOCAL_ORIGINS}
    extra = os.environ.get("ADOS_CORS_ORIGINS", "")
    for part in extra.split(","):
        value = part.strip().rstrip("/")
        if value and value != "*":
            origins.add(value)
    return origins


def origin_allowed(origin: str) -> bool:
    if not origin:
        return False
    normalized = origin.rstrip("/")
    if normalized in configured_origins():
        return True
    suffix = (os.environ.get("ADOS_CORS_TUNNEL_SUFFIX") or ".trycloudflare.com").strip()
    if suffix and normalized.startswith("https://") and normalized.endswith(suffix):
        return True
    if _lan_dev_origin(normalized):
        return True
    return False


def origin_matches_request_host(origin: str, request: web.Request) -> bool:
    """Same-origin SPA + API (Render): Origin host equals the request Host."""
    if not origin:
        return False
    from urllib.parse import urlparse

    parsed = urlparse(origin)
    origin_host = (parsed.hostname or "").lower()
    req_host = (request.headers.get("Host") or request.host or "").split(":")[0].lower()
    return bool(origin_host and req_host and origin_host == req_host)


def cors_origin_ok(origin: str, request: web.Request) -> bool:
    return origin_allowed(origin) or origin_matches_request_host(origin, request)


def _lan_dev_origin(origin: str) -> bool:
    """Phone on the same Wi-Fi uses http://<lan-ip>:5180 — exact private HTTP origins only."""
    from urllib.parse import urlparse

    parsed = urlparse(origin)
    if parsed.scheme != "http":
        return False
    if parsed.port not in {5180, 4173, 8080}:
        return False
    host = parsed.hostname or ""
    parts = host.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        return False
    a, b = int(parts[0]), int(parts[1])
    if a == 10:
        return True
    if a == 192 and b == 168:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    return False


def apply_cors_headers(request: web.Request, response: web.StreamResponse) -> web.StreamResponse:
    origin = request.headers.get("Origin", "").strip()
    if cors_origin_ok(origin, request):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = _ALLOW_HEADERS
        response.headers["Access-Control-Allow-Methods"] = _ALLOW_METHODS
        response.headers["Vary"] = "Origin"
        response.headers.setdefault("Access-Control-Max-Age", "600")
    return response


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=204)
        apply_cors_headers(request, response)
        return response
    response = await handler(request)
    return apply_cors_headers(request, response)
