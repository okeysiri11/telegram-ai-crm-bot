"""API helpers and recruiter auth for Recruiting Ops.

HMAC ingest stays public (signature checked in the handler). Recruiter READ/WRITE
routes require the existing platform identity (Bearer JWT / API key). Header-only
X-Role is limited to ALLOW_HEADER_AUTH (development/tests), matching Platform Builder.
"""

from __future__ import annotations

import logging

from aiohttp import web

from services.recruiting_ops.rbac import normalize_role

logger = logging.getLogger(__name__)

OPS_PREFIX = "/api/recruiting-ops/"

_OWNER_ROLE_MARKERS = frozenset(
    {
        "owner",
        "platform_owner",
        "platform_admin",
        "company_owner",
        "administrator",
        "admin",
    }
)


def json_response(data, *, status: int = 200, retry_after: int | None = None) -> web.Response:
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
    return web.json_response(data, status=status, headers=headers)


def _allow_header_auth() -> bool:
    try:
        from platform_configuration.configuration_center import configuration_center

        return bool(configuration_center.settings.security.allow_header_auth)
    except Exception:
        return True


def is_recruiting_ops_path(path: str) -> bool:
    return path.startswith(OPS_PREFIX)


def is_public_recruiting_path(request: web.Request) -> bool:
    """Unsigned-by-JWT surfaces: HMAC ingest, provider webhooks, OAuth callback, liveness."""
    path = request.path
    method = request.method.upper()
    if method == "OPTIONS":
        return True
    if not is_recruiting_ops_path(path):
        return False
    if method == "GET" and path.endswith("/health"):
        return True
    if method == "POST" and path.endswith("/vanguard/leads"):
        return True
    if "/webhooks/whatsapp" in path:
        return True
    if "/oauth/" in path and path.endswith("/callback"):
        return True
    return False


def _org_label(request: web.Request) -> str:
    return (
        request.headers.get("X-Recruiting-Organization-Id")
        or request.headers.get("X-Organization-Id")
        or request.headers.get("X-Tenant-Id")
        or request.rel_url.query.get("organization_id")
        or "unset"
    )


def _is_opaque_bearer(token: str) -> bool:
    return bool(token) and token.count(".") != 2


def _as_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _roles_are_owner(roles: list[str] | None) -> bool:
    return any(str(r).strip().lower() in _OWNER_ROLE_MARKERS for r in (roles or []))


def resolve_recruiting_role(*, requested: str | None, jwt_roles: list[str] | None, owner_session: bool) -> str:
    requested_norm = normalize_role(requested)
    if owner_session or _roles_are_owner(jwt_roles):
        return requested_norm if requested else "platform_owner"
    if requested_norm in {"platform_owner", "owner"}:
        return "recruiter"
    return requested_norm


def _auth_failure(request: web.Request, *, status: int, error: str, message_ru: str, mechanism: str) -> web.Response:
    logger.info(
        "RECRUITING_AUTH_FAILURE route=%s status=%s auth_mechanism=%s org=%s",
        request.path,
        status,
        mechanism,
        _org_label(request),
    )
    return json_response({"ok": False, "error": error, "message_ru": message_ru}, status=status)


async def _authenticate_jwt_stateless(token: str):
    """Verify platform JWT without in-process session_manager (demo-auth / multi-worker)."""
    from platform_identity.exceptions import TokenError
    from platform_identity.jwt_service import jwt_service
    from platform_identity.models import AuthMethod, Principal

    try:
        claims = jwt_service.verify_access_token(token)
    except TokenError:
        return None
    roles = [str(r) for r in (claims.get("roles") or [])]
    return Principal(
        principal_id=str(claims.get("sub") or claims.get("user_id") or "jwt"),
        auth_method=AuthMethod.JWT,
        roles=roles,
        permissions=[str(p) for p in (claims.get("permissions") or [])],
        telegram_id=_as_int(claims.get("telegram_id")),
        user_id=str(claims.get("user_id") or "") or None,
        email=str(claims.get("email") or "") or None,
        tenant_id=str(claims.get("tenant_id") or "") or None,
        session_id=str(claims.get("session_id") or "") or None,
    )


@web.middleware
async def recruiting_auth_middleware(request: web.Request, handler):
    if not is_recruiting_ops_path(request.path):
        return await handler(request)
    if is_public_recruiting_path(request):
        request["recruiting_auth_source"] = "public"
        return await handler(request)

    auth_header = request.headers.get("Authorization", "")
    bearer = auth_header[7:].strip() if auth_header.lower().startswith("bearer ") else ""
    api_key = request.headers.get("X-API-Key", "").strip()
    requested_role = request.headers.get("X-Role") or request.rel_url.query.get("role")

    if bearer or api_key:
        if bearer and _is_opaque_bearer(bearer) and not api_key:
            # Sprint 40.4 ISAM opaque access_* tokens — authenticated session, not anonymous.
            request["principal"] = f"isam:{bearer[:12]}"
            request["iam_principal"] = None
            request["recruiting_auth_source"] = "isam_opaque"
            request["recruiting_role"] = resolve_recruiting_role(
                requested=requested_role,
                jwt_roles=None,
                owner_session=normalize_role(requested_role) in {"owner", "platform_owner"},
            )
            return await handler(request)

        if api_key:
            try:
                from platform_identity.identity_service import identity_service

                principal = await identity_service.authenticate_request(request)
            except Exception:
                return _auth_failure(
                    request,
                    status=401,
                    error="invalid_token",
                    message_ru="Сессия недействительна. Войдите снова.",
                    mechanism="invalid_api_key",
                )
            request["iam_principal"] = principal
            request["principal"] = principal.principal_id
            request["recruiting_auth_source"] = "api_key"
            request["recruiting_role"] = resolve_recruiting_role(
                requested=requested_role,
                jwt_roles=list(principal.roles or []),
                owner_session=principal.is_owner,
            )
            return await handler(request)

        principal = await _authenticate_jwt_stateless(bearer)
        if principal is None:
            return _auth_failure(
                request,
                status=401,
                error="invalid_token",
                message_ru="Сессия недействительна. Войдите снова.",
                mechanism="invalid_jwt",
            )
        request["iam_principal"] = principal
        request["principal"] = principal.principal_id
        request["recruiting_auth_source"] = "jwt"
        request["recruiting_role"] = resolve_recruiting_role(
            requested=requested_role,
            jwt_roles=list(principal.roles or []),
            owner_session=principal.is_owner,
        )
        return await handler(request)

    if requested_role or request.headers.get("X-Principal"):
        if not _allow_header_auth():
            return _auth_failure(
                request,
                status=401,
                error="authentication_required",
                message_ru="Требуется вход в систему.",
                mechanism="header_auth_disabled",
            )
        request["principal"] = request.headers.get("X-Principal")
        request["recruiting_auth_source"] = "header_compat"
        request["recruiting_role"] = normalize_role(requested_role)
        return await handler(request)

    if not _allow_header_auth():
        return _auth_failure(
            request,
            status=401,
            error="authentication_required",
            message_ru="Требуется вход в систему.",
            mechanism="missing_bearer",
        )
    request["recruiting_auth_source"] = "header_compat"
    request["recruiting_role"] = normalize_role(requested_role)
    return await handler(request)
