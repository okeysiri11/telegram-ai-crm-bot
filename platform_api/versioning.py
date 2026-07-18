# API versioning, deprecation, and legacy compatibility adapters.

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import web

from platform_api.contracts import API_CONTRACT_VERSION, PLATFORM_API_VERSION

logger = logging.getLogger(__name__)

MANAGEMENT_V1_PREFIX = f"/management/{PLATFORM_API_VERSION}"
PUBLIC_V1_PREFIX = f"/api/{PLATFORM_API_VERSION}"
LEGACY_PUBLIC_PREFIX = "/v1"
LEGACY_MANAGEMENT_PREFIX = "/management"

DEPRECATION_HEADER = "Deprecation"
SUNSET_HEADER = "Sunset"
LINK_HEADER = "Link"
SUCCESSOR_HEADER = "X-API-Successor"

Handler = Callable[..., Awaitable[web.Response] | web.Response]

_OPENAPI_V1_PATHS: dict[str, dict[str, Any]] = {}


def management_path(suffix: str) -> str:
    suffix = suffix.lstrip("/")
    return f"{MANAGEMENT_V1_PREFIX}/{suffix}" if suffix else MANAGEMENT_V1_PREFIX


def legacy_management_path(suffix: str) -> str:
    suffix = suffix.lstrip("/")
    return f"{LEGACY_MANAGEMENT_PREFIX}/{suffix}" if suffix else LEGACY_MANAGEMENT_PREFIX


def public_path(suffix: str) -> str:
    suffix = suffix.lstrip("/")
    return f"{PUBLIC_V1_PREFIX}/{suffix}" if suffix else PUBLIC_V1_PREFIX


def legacy_public_path(suffix: str) -> str:
    suffix = suffix.lstrip("/")
    return f"{LEGACY_PUBLIC_PREFIX}/{suffix}" if suffix else LEGACY_PUBLIC_PREFIX


def deprecated(
    *,
    since: str = API_CONTRACT_VERSION,
    successor: str | None = None,
    sunset: str | None = None,
) -> Callable[[Handler], Handler]:
    """Attach deprecation metadata to a route handler."""

    def decorator(handler: Handler) -> Handler:
        @functools.wraps(handler)
        async def wrapper(request: web.Request, *args: Any, **kwargs: Any) -> web.Response:
            response = handler(request, *args, **kwargs)
            if hasattr(response, "__await__"):
                response = await response
            return apply_deprecation_headers(
                response,
                since=since,
                successor=successor or getattr(handler, "__deprecated_successor__", None),
                sunset=sunset,
            )

        wrapper.__deprecated__ = True  # type: ignore[attr-defined]
        wrapper.__deprecated_since__ = since  # type: ignore[attr-defined]
        wrapper.__deprecated_successor__ = successor  # type: ignore[attr-defined]
        wrapper.__deprecated_sunset__ = sunset  # type: ignore[attr-defined]
        return wrapper

    return decorator


def apply_deprecation_headers(
    response: web.Response,
    *,
    since: str,
    successor: str | None = None,
    sunset: str | None = None,
) -> web.Response:
    response.headers[DEPRECATION_HEADER] = f'version="{since}"'
    if sunset:
        response.headers[SUNSET_HEADER] = sunset
    if successor:
        response.headers[SUCCESSOR_HEADER] = successor
        response.headers[LINK_HEADER] = f'<{successor}>; rel="successor-version"'
    return response


def wrap_legacy_handler(handler: Handler, *, successor: str, since: str = API_CONTRACT_VERSION) -> Handler:
    return deprecated(since=since, successor=successor)(handler)


def record_openapi_v1_path(
    path: str,
    method: str,
    *,
    summary: str,
    required_role: str | None = None,
    tags: list[str] | None = None,
) -> None:
    if not path.startswith(MANAGEMENT_V1_PREFIX):
        return
    methods = _OPENAPI_V1_PATHS.setdefault(path, {})
    methods[method.lower()] = {
        "summary": summary,
        "tags": tags or ["management"],
        "security": [{"BearerAuth": []}, {"ApiKeyAuth": []}],
        "responses": {
            "200": {
                "description": "Standard API envelope",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ApiEnvelope"},
                    }
                },
            }
        },
        **({"x-required-role": required_role} if required_role else {}),
    }


def build_management_openapi_spec() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Platform Management API",
            "version": API_CONTRACT_VERSION,
            "description": f"Frozen management API ({MANAGEMENT_V1_PREFIX}).",
        },
        "servers": [{"url": "/"}],
        "components": {
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            },
            "schemas": {
                "ApiEnvelope": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "request_id": {"type": "string", "format": "uuid"},
                        "api_version": {"type": "string"},
                        "contract_version": {"type": "string"},
                        "data": {},
                        "errors": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "success",
                        "timestamp",
                        "request_id",
                        "api_version",
                        "contract_version",
                        "data",
                        "errors",
                    ],
                },
                "PaginationMeta": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "page_size": {"type": "integer"},
                        "total": {"type": "integer"},
                        "has_next": {"type": "boolean"},
                    },
                },
            },
        },
        "paths": dict(_OPENAPI_V1_PATHS),
    }


def build_public_openapi_spec() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Platform Public API",
            "version": API_CONTRACT_VERSION,
            "description": f"Frozen public API ({PUBLIC_V1_PREFIX}).",
        },
        "servers": [{"url": "/"}],
        "paths": _PUBLIC_OPENAPI_PATHS,
        "components": {
            "schemas": {
                "ApiEnvelope": build_management_openapi_spec()["components"]["schemas"]["ApiEnvelope"],
            }
        },
    }


_PUBLIC_OPENAPI_PATHS: dict[str, dict[str, Any]] = {}


def record_public_openapi_path(path: str, method: str, *, summary: str) -> None:
    if not path.startswith(PUBLIC_V1_PREFIX):
        return
    methods = _PUBLIC_OPENAPI_PATHS.setdefault(path, {})
    methods[method.lower()] = {"summary": summary}


def reset_openapi_registry() -> None:
    _OPENAPI_V1_PATHS.clear()
    _PUBLIC_OPENAPI_PATHS.clear()


def register_dual_prefix_routes(
    app: web.Application,
    *,
    route_specs: list[tuple[str, str, Handler]],
    v1_prefix: str,
    legacy_prefix: str,
    since: str = API_CONTRACT_VERSION,
) -> None:
    """Register handlers on v1 prefix and legacy prefix with deprecation headers."""
    for method, rel, handler in route_specs:
        rel = rel.strip("/")
        v1_path = f"{v1_prefix}/{rel}" if rel else v1_prefix
        legacy_path = f"{legacy_prefix}/{rel}" if rel else legacy_prefix
        getattr(app.router, f"add_{method.lower()}")(v1_path, handler)
        if legacy_path != v1_path:
            legacy_handler = wrap_legacy_handler(handler, successor=v1_path, since=since)
            getattr(app.router, f"add_{method.lower()}")(legacy_path, legacy_handler)


def register_legacy_public_alias(
    app: web.Application,
    *,
    method: str,
    legacy_path: str,
    v1_path: str,
    handler: Handler,
) -> None:
    getattr(app.router, f"add_{method.lower()}")(
        v1_path,
        handler,
    )
    record_public_openapi_path(v1_path, method, summary=v1_path)
    if legacy_path != v1_path:
        getattr(app.router, f"add_{method.lower()}")(
            legacy_path,
            wrap_legacy_handler(handler, successor=v1_path),
        )
