# Management API router — REST orchestration layer (no business logic).

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_management.exceptions import ManagementAPIError, ManagementNotFoundError
from platform_management.management_context import ManagementContext
from platform_management.management_service import management_service
from platform_management.permissions import ManagementRole, require_role
from platform_management.response_models import error_response, success_response

from platform_api.versioning import (
    MANAGEMENT_V1_PREFIX,
    build_management_openapi_spec,
    legacy_management_path,
    record_openapi_v1_path,
    wrap_legacy_handler,
)

logger = logging.getLogger(__name__)


def _route(
    app: web.Application,
    method: str,
    suffix: str,
    handler,
    *,
    role: ManagementRole,
    summary: str,
) -> None:
    v1_path = f"{MANAGEMENT_V1_PREFIX}/{suffix.lstrip('/')}"
    legacy_path = legacy_management_path(suffix)
    record_openapi_v1_path(v1_path, method, summary=summary, required_role=role.value)
    getattr(app.router, f"add_{method.lower()}")(v1_path, handler)
    if legacy_path != v1_path:
        getattr(app.router, f"add_{method.lower()}")(
            legacy_path,
            wrap_legacy_handler(handler, successor=v1_path),
        )


async def _json_body(request: web.Request) -> dict[str, Any]:
    try:
        return await request.json()
    except Exception:
        return {}


def _ok(data: Any, ctx: ManagementContext, *, status: int = 200) -> web.Response:
    envelope = success_response(data, request_id=ctx.request_id, status=status)
    if ctx.audit_id:
        envelope.headers["X-Audit-Id"] = ctx.audit_id
    return envelope


def _handle_api_error(exc: Exception, ctx: ManagementContext) -> web.Response:
    if isinstance(exc, ManagementAPIError):
        return error_response(exc.message, request_id=ctx.request_id, status=exc.status)
    return error_response(str(exc), request_id=ctx.request_id, status=500)


# ---- SYSTEM ----

@require_role(ManagementRole.READ_ONLY)
async def system_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.system_info(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def health_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.health(), ctx)


# ---- CONFIGURATION ----

@require_role(ManagementRole.READ_ONLY)
async def config_list_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    section = request.query.get("section")
    data = await management_service.config_list(section=section)
    return _ok({"section": section, "configuration": data}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def config_get_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    key = request.match_info["key"]
    value = await management_service.config_get(key, actor_telegram_id=ctx.actor_telegram_id)
    return _ok({"key": key, "value": value}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def config_set_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    key = request.match_info["key"]
    body = await _json_body(request)
    try:
        result = await management_service.config_set(
            key,
            body.get("value"),
            changed_by=body.get("changed_by") or str(ctx.actor_telegram_id),
            reason=body.get("reason"),
            actor_telegram_id=ctx.actor_telegram_id,
        )
    except Exception as exc:
        return _handle_api_error(exc, ctx)
    return _ok(result, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def config_delete_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    key = request.match_info["key"]
    body = await _json_body(request)
    try:
        result = await management_service.config_delete(
            key,
            changed_by=body.get("changed_by") or str(ctx.actor_telegram_id),
            reason=body.get("reason"),
            actor_telegram_id=ctx.actor_telegram_id,
        )
    except Exception as exc:
        return _handle_api_error(exc, ctx)
    if result is None:
        return error_response("Key not found", request_id=ctx.request_id, status=404)
    return _ok(result, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def config_rollback_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    key = request.match_info["key"]
    body = await _json_body(request)
    version = body.get("version")
    if version is None:
        return error_response("version is required", request_id=ctx.request_id, status=400)
    try:
        result = await management_service.config_rollback(
            key,
            int(version),
            changed_by=body.get("changed_by") or str(ctx.actor_telegram_id),
            reason=body.get("reason"),
            actor_telegram_id=ctx.actor_telegram_id,
        )
    except Exception as exc:
        return _handle_api_error(exc, ctx)
    if result is None:
        return error_response("Version not found", request_id=ctx.request_id, status=404)
    return _ok(result, ctx)


@require_role(ManagementRole.READ_ONLY)
async def config_history_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    key = request.match_info["key"]
    limit = int(request.query.get("limit", "50"))
    history = await management_service.config_history(key, limit=limit)
    return _ok({"key": key, "history": history}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def config_validate_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    body = await _json_body(request)
    try:
        result = await management_service.config_validate(body.get("payload"))
    except Exception as exc:
        return _handle_api_error(exc, ctx)
    return _ok(result, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def config_import_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    body = await _json_body(request)
    payload = body.get("payload") or body
    try:
        result = await management_service.config_import(
            payload,
            changed_by=body.get("changed_by") or str(ctx.actor_telegram_id),
            reason=body.get("reason"),
            actor_telegram_id=ctx.actor_telegram_id,
        )
    except Exception as exc:
        return _handle_api_error(exc, ctx)
    return _ok(result, ctx)


@require_role(ManagementRole.READ_ONLY)
async def config_export_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.config_export(), ctx)


# ---- VERTICALS ----

@require_role(ManagementRole.READ_ONLY)
async def verticals_list_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok({"verticals": await management_service.list_verticals()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def vertical_get_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    code = request.match_info["code"]
    try:
        return _ok(await management_service.get_vertical(code), ctx)
    except ManagementNotFoundError as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=404)


@require_role(ManagementRole.ADMINISTRATOR)
async def vertical_enable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    code = request.match_info["code"]
    try:
        return _ok(await management_service.vertical_enable(code, actor_telegram_id=ctx.actor_telegram_id), ctx)
    except Exception as exc:
        return _handle_api_error(exc, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def vertical_disable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    code = request.match_info["code"]
    try:
        return _ok(await management_service.vertical_disable(code, actor_telegram_id=ctx.actor_telegram_id), ctx)
    except Exception as exc:
        return _handle_api_error(exc, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def vertical_reload_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    code = request.match_info["code"]
    return _ok(await management_service.vertical_reload(code), ctx)


# ---- WORKFLOWS ----

@require_role(ManagementRole.READ_ONLY)
async def workflows_list_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.list_workflows(), ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def workflows_reload_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.reload_workflows(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def workflows_validate_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.validate_workflows(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def workflows_statistics_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.workflow_statistics(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def workflows_executions_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.workflow_executions(), ctx)


# ---- MANAGERS ----

@require_role(ManagementRole.READ_ONLY)
async def managers_overview_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    vertical = request.query.get("vertical")
    return _ok(await management_service.managers_overview(vertical=vertical), ctx)


# ---- REQUESTS ----

@require_role(ManagementRole.READ_ONLY)
async def requests_overview_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.requests_overview(), ctx)


# ---- EVENT BUS ----

@require_role(ManagementRole.READ_ONLY)
async def event_bus_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.event_bus_status(), ctx)


# ---- AUDIT ----

@require_role(ManagementRole.READ_ONLY)
async def audit_search_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    from platform_api.contracts import AuditSearchData
    from platform_api.pagination import PaginatedResponse, PaginationMeta, PaginationParams

    params = PaginationParams.from_query(dict(request.query))
    rows = await management_service.audit_search(
        event_type=request.query.get("event_type"),
        entity_type=request.query.get("entity_type"),
        entity_id=request.query.get("entity_id"),
        limit=params.page_size,
    )
    total = len(rows)
    page_rows = rows[params.offset : params.offset + params.page_size]
    payload = PaginatedResponse(
        items=page_rows,
        pagination=PaginationMeta.build(page=params.page, page_size=params.page_size, total=total),
    )
    data = AuditSearchData(
        entries=page_rows,
        count=len(page_rows),
        pagination=payload.pagination.model_dump(),
    )
    return _ok(data.model_dump(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def audit_export_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    payload = await management_service.audit_export(
        event_type=request.query.get("event_type"),
        limit=int(request.query.get("limit", "500")),
    )
    return _ok(payload, ctx)


@require_role(ManagementRole.READ_ONLY)
async def audit_history_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    rows = await management_service.audit_history(
        request_id=request.query.get("request_id"),
        manager_id=request.query.get("manager_id"),
        limit=int(request.query.get("limit", "200")),
    )
    return _ok({"history": rows, "count": len(rows)}, ctx)


# ---- KPI ----

@require_role(ManagementRole.READ_ONLY)
async def kpi_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    period = request.query.get("period", "month")
    return _ok(await management_service.kpi_current(period=period), ctx)


# ---- FEATURE FLAGS ----

@require_role(ManagementRole.READ_ONLY)
async def feature_flags_list_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.feature_flags_list(), ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def feature_flags_enable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    key = request.match_info["key"]
    try:
        return _ok(
            await management_service.feature_flag_enable(key, actor_telegram_id=ctx.actor_telegram_id),
            ctx,
        )
    except Exception as exc:
        return _handle_api_error(exc, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def feature_flags_disable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    key = request.match_info["key"]
    try:
        return _ok(
            await management_service.feature_flag_disable(key, actor_telegram_id=ctx.actor_telegram_id),
            ctx,
        )
    except Exception as exc:
        return _handle_api_error(exc, ctx)


@require_role(ManagementRole.READ_ONLY)
async def feature_flags_validate_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return _ok(await management_service.feature_flags_validate(), ctx)


# ---- OPERATIONS DASHBOARD ----

@require_role(ManagementRole.READ_ONLY)
async def dashboard_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    from platform_operations.operations_service import operations_service

    refresh = request.query.get("refresh", "").lower() in {"1", "true", "yes"}
    if refresh:
        data = await operations_service.refresh_dashboard()
    else:
        use_cache = request.query.get("no_cache", "").lower() not in {"1", "true", "yes"}
        data = await operations_service.get_dashboard(use_cache=use_cache)
    return _ok(data, ctx)


@require_role(ManagementRole.READ_ONLY)
async def dashboard_widget_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    from platform_operations.operations_service import operations_service

    widget_id = request.match_info["widget_id"]
    no_cache = request.query.get("no_cache", "").lower() in {"1", "true", "yes"}
    try:
        data = await operations_service.get_widget(widget_id, use_cache=not no_cache)
    except Exception as exc:
        return _handle_api_error(exc, ctx)
    return _ok(data, ctx)


@require_role(ManagementRole.READ_ONLY)
async def dashboard_metrics_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    from platform_operations.operations_service import operations_service

    period = request.query.get("period", "month")
    return _ok(await operations_service.get_metrics(period=period), ctx)


@require_role(ManagementRole.READ_ONLY)
async def dashboard_event_timeline_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    from platform_operations.operations_service import operations_service

    return _ok(
        await operations_service.get_event_timeline(
            event_type=request.query.get("event_type"),
            limit=int(request.query.get("limit", "50")),
        ),
        ctx,
    )


@require_role(ManagementRole.READ_ONLY)
async def realtime_status_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    from platform_realtime.realtime_hub import realtime_hub

    return _ok(await realtime_hub.status(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def dashboard_audit_timeline_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    from platform_operations.operations_service import operations_service

    return _ok(
        await operations_service.get_audit_timeline(
            category=request.query.get("category"),
            limit=int(request.query.get("limit", "50")),
        ),
        ctx,
    )


# ---- OPENAPI ----

async def openapi_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    return web.json_response(build_management_openapi_spec())


async def swagger_ui_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    html = f"""<!DOCTYPE html>
<html><head><title>Platform Management API v1</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head><body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({{url: '{MANAGEMENT_V1_PREFIX}/openapi.json', dom_id: '#swagger-ui'}});
</script></body></html>"""
    return web.Response(text=html, content_type="text/html")


def register_management_routes(app: web.Application) -> None:
    _route(app, "GET", "system", system_handler, role=ManagementRole.READ_ONLY, summary="Platform system info")
    _route(app, "GET", "health", health_handler, role=ManagementRole.READ_ONLY, summary="Subsystem health")

    _route(app, "GET", "configuration", config_list_handler, role=ManagementRole.READ_ONLY, summary="List configuration")
    _route(app, "GET", "configuration/export", config_export_handler, role=ManagementRole.READ_ONLY, summary="Export configuration")
    _route(app, "POST", "configuration/validate", config_validate_handler, role=ManagementRole.READ_ONLY, summary="Validate configuration")
    _route(app, "POST", "configuration/import", config_import_handler, role=ManagementRole.ADMINISTRATOR, summary="Import configuration")
    _route(app, "GET", "configuration/{key:.+}/history", config_history_handler, role=ManagementRole.READ_ONLY, summary="Configuration history")
    _route(app, "POST", "configuration/{key:.+}/rollback", config_rollback_handler, role=ManagementRole.ADMINISTRATOR, summary="Rollback configuration")
    _route(app, "GET", "configuration/{key:.+}", config_get_handler, role=ManagementRole.READ_ONLY, summary="Get configuration key")
    _route(app, "PUT", "configuration/{key:.+}", config_set_handler, role=ManagementRole.ADMINISTRATOR, summary="Set configuration key")
    _route(app, "POST", "configuration/{key:.+}", config_set_handler, role=ManagementRole.ADMINISTRATOR, summary="Set configuration key (POST)")
    _route(app, "DELETE", "configuration/{key:.+}", config_delete_handler, role=ManagementRole.ADMINISTRATOR, summary="Delete configuration key")

    _route(app, "GET", "verticals", verticals_list_handler, role=ManagementRole.READ_ONLY, summary="List verticals")
    _route(app, "GET", "verticals/{code}", vertical_get_handler, role=ManagementRole.READ_ONLY, summary="Get vertical")
    _route(app, "POST", "verticals/{code}/enable", vertical_enable_handler, role=ManagementRole.ADMINISTRATOR, summary="Enable vertical")
    _route(app, "POST", "verticals/{code}/disable", vertical_disable_handler, role=ManagementRole.ADMINISTRATOR, summary="Disable vertical")
    _route(app, "POST", "verticals/{code}/reload", vertical_reload_handler, role=ManagementRole.ADMINISTRATOR, summary="Reload vertical")

    _route(app, "GET", "workflows", workflows_list_handler, role=ManagementRole.READ_ONLY, summary="List workflows")
    _route(app, "POST", "workflows/reload", workflows_reload_handler, role=ManagementRole.ADMINISTRATOR, summary="Reload workflows")
    _route(app, "GET", "workflows/validate", workflows_validate_handler, role=ManagementRole.READ_ONLY, summary="Validate workflows")
    _route(app, "GET", "workflows/statistics", workflows_statistics_handler, role=ManagementRole.READ_ONLY, summary="Workflow statistics")
    _route(app, "GET", "workflows/executions", workflows_executions_handler, role=ManagementRole.READ_ONLY, summary="Active workflow executions")

    _route(app, "GET", "managers", managers_overview_handler, role=ManagementRole.READ_ONLY, summary="Managers overview")
    _route(app, "GET", "requests", requests_overview_handler, role=ManagementRole.READ_ONLY, summary="Requests overview")
    _route(app, "GET", "events", event_bus_handler, role=ManagementRole.READ_ONLY, summary="Event bus status")

    _route(app, "GET", "audit", audit_search_handler, role=ManagementRole.READ_ONLY, summary="Search audit")
    _route(app, "GET", "audit/export", audit_export_handler, role=ManagementRole.READ_ONLY, summary="Export audit")
    _route(app, "GET", "audit/history", audit_history_handler, role=ManagementRole.READ_ONLY, summary="Audit history")

    _route(app, "GET", "kpi", kpi_handler, role=ManagementRole.READ_ONLY, summary="KPI dashboard")

    from platform_plugins.plugins_router import register_plugins_routes

    register_plugins_routes(app)
    from platform_ai.ai_router import register_ai_routes

    register_ai_routes(app)
    from platform_ai.skills_router import register_skills_routes

    register_skills_routes(app)
    from platform_ai.workflows_router import register_workflows_routes

    register_workflows_routes(app)
    from platform_ai.memory_router import register_memory_routes

    register_memory_routes(app)

    _route(app, "GET", "feature-flags", feature_flags_list_handler, role=ManagementRole.READ_ONLY, summary="List feature flags")
    _route(app, "POST", "feature-flags/{key:.+}/enable", feature_flags_enable_handler, role=ManagementRole.ADMINISTRATOR, summary="Enable feature flag")
    _route(app, "POST", "feature-flags/{key:.+}/disable", feature_flags_disable_handler, role=ManagementRole.ADMINISTRATOR, summary="Disable feature flag")
    _route(app, "GET", "feature-flags/validate", feature_flags_validate_handler, role=ManagementRole.READ_ONLY, summary="Validate feature flags")

    _route(app, "GET", "dashboard", dashboard_handler, role=ManagementRole.READ_ONLY, summary="Operations dashboard (all widgets)")
    _route(app, "GET", "dashboard/widgets/{widget_id}", dashboard_widget_handler, role=ManagementRole.READ_ONLY, summary="Single dashboard widget")
    _route(app, "GET", "dashboard/metrics", dashboard_metrics_handler, role=ManagementRole.READ_ONLY, summary="KPI metrics")
    _route(app, "GET", "dashboard/timeline/events", dashboard_event_timeline_handler, role=ManagementRole.READ_ONLY, summary="Event timeline")
    _route(app, "GET", "dashboard/timeline/audit", dashboard_audit_timeline_handler, role=ManagementRole.READ_ONLY, summary="Audit timeline")

    _route(app, "GET", "realtime", realtime_status_handler, role=ManagementRole.READ_ONLY, summary="Realtime connections and statistics")

    from platform_realtime.websocket_router import register_realtime_routes

    register_realtime_routes(app)

    from platform_identity.identity_router import register_identity_routes

    register_identity_routes(app)

    from platform_integrations.integration_router import register_integration_routes

    register_integration_routes(app)

    from platform_jobs.jobs_router import register_jobs_routes

    register_jobs_routes(app)

    from platform_observability.telemetry_router import register_observability_routes

    register_observability_routes(app)

    v1_openapi = f"{MANAGEMENT_V1_PREFIX}/openapi.json"
    v1_docs = f"{MANAGEMENT_V1_PREFIX}/docs"
    legacy_openapi = legacy_management_path("openapi.json")
    legacy_docs = legacy_management_path("docs")

    app.router.add_get(v1_openapi, require_role(ManagementRole.READ_ONLY)(openapi_handler))
    app.router.add_get(v1_docs, require_role(ManagementRole.READ_ONLY)(swagger_ui_handler))
    app.router.add_get(
        legacy_openapi,
        require_role(ManagementRole.READ_ONLY)(wrap_legacy_handler(openapi_handler, successor=v1_openapi)),
    )
    app.router.add_get(
        legacy_docs,
        require_role(ManagementRole.READ_ONLY)(wrap_legacy_handler(swagger_ui_handler, successor=v1_docs)),
    )

    logger.info(
        "management_api_routes_registered v1_prefix=%s legacy_compat=true",
        MANAGEMENT_V1_PREFIX,
    )
