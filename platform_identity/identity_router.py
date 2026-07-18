# IAM Management API routes — /management/identity/*

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_identity.api_keys import api_key_service
from platform_identity.audit_hooks import iam_audit
from platform_identity.identity_service import identity_service
from platform_identity.policy_engine import policy_engine
from platform_identity.session_manager import session_manager
from platform_management.management_context import ManagementContext
from platform_management.permissions import ManagementRole, require_role
from platform_management.response_models import error_response, success_response

logger = logging.getLogger(__name__)


def _ok(data: Any, ctx: ManagementContext, *, status: int = 200) -> web.Response:
    return success_response(data, request_id=ctx.request_id, status=status)


async def _json_body(request: web.Request) -> dict[str, Any]:
    try:
        return await request.json()
    except Exception:
        return {}


@require_role(ManagementRole.READ_ONLY)
async def identity_status_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(identity_service.status(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def identity_users_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok({"users": identity_service.list_users()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def identity_roles_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(identity_service.list_roles(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def identity_permissions_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(identity_service.list_permissions(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def identity_sessions_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok({"sessions": identity_service.list_sessions()}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def identity_session_revoke_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    session_id = request.match_info["session_id"]
    session = session_manager.revoke(session_id)
    return _ok({"revoked": session.to_dict()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def identity_api_keys_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok({"api_keys": identity_service.list_api_keys()}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def identity_api_keys_create_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    body = await _json_body(request)
    raw, record = api_key_service.create_key(
        name=str(body.get("name", "default")),
        scopes=list(body.get("scopes", ["management.read"])),
        telegram_id=body.get("telegram_id"),
        expires_in_days=body.get("expires_in_days", 365),
    )
    await iam_audit.log_api_key_created(actor_id=ctx.actor_telegram_id, record=record)
    return _ok({"api_key": raw, "record": record.to_dict()}, ctx, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def identity_api_keys_rotate_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    key_id = request.match_info["key_id"]
    raw, record = api_key_service.rotate_key(key_id)
    await iam_audit.log_api_key_created(actor_id=ctx.actor_telegram_id, record=record)
    return _ok({"api_key": raw, "record": record.to_dict()}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def identity_api_keys_disable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    key_id = request.match_info["key_id"]
    record = api_key_service.disable_key(key_id)
    return _ok({"disabled": record.to_dict()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def identity_policies_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok({"policies": identity_service.list_policies()}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def identity_policies_create_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    body = await _json_body(request)
    from platform_identity.models import ResourceRef

    resources = [
        ResourceRef(type=r["type"], id=r.get("id"), tenant_id=r.get("tenant_id"))
        for r in body.get("resources", [])
    ]
    policy = policy_engine.create_policy(
        name=str(body.get("name", "custom")),
        effect=str(body.get("effect", "allow")),
        permissions=list(body.get("permissions", [])),
        roles=list(body.get("roles", [])),
        principal_ids=list(body.get("principal_ids", [])),
        resources=resources,
        tenant_id=body.get("tenant_id"),
    )
    return _ok({"policy": policy.to_dict()}, ctx, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def identity_policies_delete_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    policy_id = request.match_info["policy_id"]
    removed = policy_engine.remove_policy(policy_id)
    return _ok({"removed": removed}, ctx)


async def identity_login_public_handler(request: web.Request) -> web.Response:
    import uuid

    from platform_identity.exceptions import AuthenticationError

    request_id = str(uuid.uuid4())
    body = await _json_body(request)
    try:
        telegram_id = await identity_service.authenticate_for_login(request, body)
        data = await identity_service.login(
            telegram_id,
            ip=_client_ip(request),
            device=request.headers.get("User-Agent", "unknown"),
        )
        return success_response(data, request_id=request_id)
    except AuthenticationError as exc:
        return error_response(str(exc), request_id=request_id, status=401)
    except Exception as exc:
        logger.exception("identity_login_failed")
        return error_response(str(exc), request_id=request_id, status=400)


async def identity_refresh_public_handler(request: web.Request) -> web.Response:
    import uuid

    from platform_identity.exceptions import TokenError

    request_id = str(uuid.uuid4())
    body = await _json_body(request)
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        return error_response("refresh_token required", request_id=request_id, status=400)
    try:
        return success_response(await identity_service.refresh_tokens(refresh_token), request_id=request_id)
    except TokenError as exc:
        return error_response(str(exc), request_id=request_id, status=401)


def _client_ip(request: web.Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    peer = request.transport.get_extra_info("peername") if request.transport else None
    return peer[0] if peer else "unknown"


def register_identity_routes(app: web.Application) -> None:
    prefix = "/management/identity"

    app.router.add_get(prefix, identity_status_handler)
    app.router.add_get(f"{prefix}/users", identity_users_handler)
    app.router.add_get(f"{prefix}/roles", identity_roles_handler)
    app.router.add_get(f"{prefix}/permissions", identity_permissions_handler)
    app.router.add_get(f"{prefix}/sessions", identity_sessions_handler)
    app.router.add_post(f"{prefix}/sessions/{{session_id}}/revoke", identity_session_revoke_handler)
    app.router.add_get(f"{prefix}/api-keys", identity_api_keys_handler)
    app.router.add_post(f"{prefix}/api-keys", identity_api_keys_create_handler)
    app.router.add_post(f"{prefix}/api-keys/{{key_id}}/rotate", identity_api_keys_rotate_handler)
    app.router.add_post(f"{prefix}/api-keys/{{key_id}}/disable", identity_api_keys_disable_handler)
    app.router.add_get(f"{prefix}/policies", identity_policies_handler)
    app.router.add_post(f"{prefix}/policies", identity_policies_create_handler)
    app.router.add_delete(f"{prefix}/policies/{{policy_id}}", identity_policies_delete_handler)
    app.router.add_post(f"{prefix}/login", identity_login_public_handler)
    app.router.add_post(f"{prefix}/refresh", identity_refresh_public_handler)

    logger.info("identity_api_routes_registered prefix=%s", prefix)
