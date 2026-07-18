# AI Memory & Knowledge Management API — /management/ai/memory/*

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_ai.memory.memory_service import memory_service
from platform_ai.memory.models import IndexRequest, RememberRequest, SearchMode
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


async def _check_ai_permission(ctx: ManagementContext, permission: str) -> web.Response | None:
    from platform_identity.identity_service import identity_service

    if ctx.actor_telegram_id is None:
        return error_response("actor required", request_id=ctx.request_id, status=403)
    principal = await identity_service.authenticate_telegram(ctx.actor_telegram_id)
    if not await identity_service.authorize(principal, permission):
        return error_response("permission denied", request_id=ctx.request_id, status=403)
    return None


@require_role(ManagementRole.READ_ONLY)
async def memory_status_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    return _ok({"statistics": memory_service.statistics()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def memory_recall_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    memory_id = request.match_info.get("memory_id") or request.query.get("memory_id")
    key = request.query.get("key")
    plugin_id = request.query.get("plugin_id")
    user_id = request.query.get("user_id")
    try:
        scope = {k: v for k, v in {"plugin_id": plugin_id, "user_id": user_id}.items() if v}
        data = memory_service.recall(memory_id, key=key, **scope)
        return _ok({"memories": data if isinstance(data, list) else [data]}, ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=404)


@require_role(ManagementRole.ADMINISTRATOR)
async def memory_remember_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.use")
    if denied:
        return denied
    body = await _json_body(request)
    req = RememberRequest(
        content=body.get("content", ""),
        memory_type=body.get("memory_type", "conversation"),
        key=body.get("key", ""),
        plugin_id=body.get("plugin_id"),
        user_id=body.get("user_id") or (str(ctx.actor_telegram_id) if ctx.actor_telegram_id else None),
        workflow_id=body.get("workflow_id"),
        session_id=body.get("session_id"),
        metadata=body.get("metadata", {}),
    )
    result = await memory_service.remember(req)
    return _ok(result, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def memory_forget_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.admin")
    if denied:
        return denied
    memory_id = request.match_info.get("memory_id")
    if not memory_id:
        return error_response("memory_id required", request_id=ctx.request_id, status=400)
    return _ok(await memory_service.forget(memory_id), ctx)


@require_role(ManagementRole.READ_ONLY)
async def memory_search_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    body = await _json_body(request) if request.method == "POST" else {}
    query = body.get("query") or request.query.get("q", "")
    if not query:
        return error_response("query required", request_id=ctx.request_id, status=400)
    result = await memory_service.search(
        query,
        mode=body.get("mode") or request.query.get("mode", SearchMode.HYBRID.value),
        limit=int(body.get("limit") or request.query.get("limit", 10)),
        plugin_id=body.get("plugin_id") or request.query.get("plugin_id"),
        user_id=body.get("user_id") or request.query.get("user_id"),
    )
    return _ok(result, ctx)


@require_role(ManagementRole.READ_ONLY)
async def knowledge_list_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    return _ok({"documents": memory_service.list_documents()}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def knowledge_index_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.use")
    if denied:
        return denied
    body = await _json_body(request)
    req = IndexRequest(
        title=body.get("title", "Untitled"),
        content=body.get("content", ""),
        doc_type=body.get("doc_type", "txt"),
        plugin_id=body.get("plugin_id"),
        tags=body.get("tags", []),
        metadata=body.get("metadata", {}),
        chunk_strategy=body.get("chunk_strategy", "paragraph"),
    )
    result = await memory_service.index(req, provider_id=body.get("provider_id"))
    return _ok(result, ctx, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def knowledge_rebuild_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.admin")
    if denied:
        return denied
    body = await _json_body(request)
    result = await memory_service.rebuild_index(body.get("document_id"), provider_id=body.get("provider_id"))
    return _ok(result, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def knowledge_delete_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.admin")
    if denied:
        return denied
    document_id = request.match_info.get("document_id")
    if not document_id:
        return error_response("document_id required", request_id=ctx.request_id, status=400)
    return _ok(await memory_service.delete_knowledge(document_id), ctx)


def register_memory_routes(app: web.Application) -> None:
    prefix = "/management/ai/memory"

    app.router.add_get(prefix, memory_status_handler)
    app.router.add_get(f"{prefix}/statistics", memory_status_handler)
    app.router.add_get(f"{prefix}/recall", memory_recall_handler)
    app.router.add_get(f"{prefix}/recall/{{memory_id}}", memory_recall_handler)
    app.router.add_post(f"{prefix}/remember", memory_remember_handler)
    app.router.add_delete(f"{prefix}/{{memory_id}}", memory_forget_handler)
    app.router.add_get(f"{prefix}/search", memory_search_handler)
    app.router.add_post(f"{prefix}/search", memory_search_handler)

    kb = f"{prefix}/knowledge"
    app.router.add_get(kb, knowledge_list_handler)
    app.router.add_post(f"{kb}/index", knowledge_index_handler)
    app.router.add_post(f"{kb}/rebuild", knowledge_rebuild_handler)
    app.router.add_delete(f"{kb}/{{document_id}}", knowledge_delete_handler)
    app.router.add_get(f"{kb}/search", memory_search_handler)
    app.router.add_post(f"{kb}/search", memory_search_handler)

    logger.info("memory_api_routes_registered prefix=%s", prefix)
