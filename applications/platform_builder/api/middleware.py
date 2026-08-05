"""API middleware — Platform Builder (Sprint 30.0 live identity + header fallback).

Auth order:
1. Authorization Bearer JWT or X-API-Key → live identity (preferred)
2. X-Principal / X-Platform-Role headers → only when ALLOW_HEADER_AUTH is true
   (default: on in non-production, off in production unless explicitly enabled)

Backward compatible with existing Platform Builder tests that send role headers in development.
"""

from __future__ import annotations

import logging

from aiohttp import web

logger = logging.getLogger(__name__)


def json_response(data, *, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


def _allow_header_auth() -> bool:
    try:
        from platform_configuration.configuration_center import configuration_center

        return bool(configuration_center.settings.security.allow_header_auth)
    except Exception:
        return True


@web.middleware
async def auth_middleware(request: web.Request, handler):
    request["principal"] = None
    request["platform_role"] = None
    request["auth_source"] = None
    request["iam_principal"] = None

    auth_header = request.headers.get("Authorization", "")
    api_key = request.headers.get("X-API-Key", "").strip()
    has_live_creds = auth_header.startswith("Bearer ") or bool(api_key)

    if has_live_creds:
        try:
            from platform_identity.identity_service import identity_service

            principal = await identity_service.authenticate_request(request)
            request["iam_principal"] = principal
            request["principal"] = principal.principal_id
            request["platform_role"] = (principal.roles[0] if principal.roles else None)
            request["auth_source"] = "jwt_or_api_key"
            return await handler(request)
        except Exception as exc:
            logger.info("platform_builder_live_auth_failed: %s", exc)
            return web.json_response(
                {"success": False, "error": "authentication_required", "detail": str(exc)},
                status=401,
            )

    header_principal = request.headers.get("X-Principal")
    header_role = request.headers.get("X-Platform-Role") or request.headers.get("X-Role")
    if header_principal or header_role:
        if not _allow_header_auth():
            return web.json_response(
                {
                    "success": False,
                    "error": "header_auth_disabled",
                    "detail": "Provide Authorization Bearer JWT or X-API-Key (TD-08)",
                },
                status=401,
            )
        request["principal"] = header_principal
        request["platform_role"] = header_role
        request["auth_source"] = "header_compat"
        return await handler(request)

    # Unauthenticated — handlers that need roles continue to see None (same as before)
    return await handler(request)
