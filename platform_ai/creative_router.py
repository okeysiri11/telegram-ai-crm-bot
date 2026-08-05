"""Creative Factory HTTP API — Sprint 36.9.

/api/creative/*
/api/campaigns/*
/api/media/*
/management/v1/creative/*
"""

from __future__ import annotations

from aiohttp import web

from platform_ai.creative_service import creative_factory_service as cfs
from platform_management.permissions import ManagementRole, require_role


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": cfs.status()})


@require_role(ManagementRole.READ_ONLY)
async def statistics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": cfs.statistics()})


@require_role(ManagementRole.READ_ONLY)
async def analytics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": cfs.analytics_dashboard()})


@require_role(ManagementRole.READ_ONLY)
async def timeline_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    data = cfs.timeline(limit=limit)
    return web.json_response({"success": True, "data": {"events": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def brands_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = cfs.list_brands()
    return web.json_response({"success": True, "data": {"brands": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def brands_upsert_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = cfs.upsert_brand(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def brand_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = cfs.get_brand(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def templates_handler(request: web.Request, ctx=None) -> web.Response:
    data = cfs.list_templates(creative_type=request.query.get("creative_type"))
    return web.json_response({"success": True, "data": {"templates": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def projects_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = cfs.list_projects()
    return web.json_response({"success": True, "data": {"projects": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def projects_create_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = cfs.create_project(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def generate_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await cfs.generate(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def assets_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = cfs.list_assets(
        creative_type=request.query.get("creative_type"),
        status=request.query.get("status"),
    )
    return web.json_response({"success": True, "data": {"assets": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def asset_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = cfs.get_asset(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def asset_review_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        data = cfs.review_asset(request.match_info["id"], body if isinstance(body, dict) else {})
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def asset_version_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = cfs.version_asset(request.match_info["id"], body)
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def search_handler(request: web.Request, ctx=None) -> web.Response:
    q = request.query.get("q") or request.query.get("query") or ""
    limit = int(request.query.get("limit") or 10)
    data = cfs.search(q, limit=limit)
    return web.json_response({"success": True, "data": {"hits": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def search_post_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = cfs.search(str(body.get("query") or body.get("q") or ""), limit=int(body.get("limit") or 10))
    return web.json_response({"success": True, "data": {"hits": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def providers_handler(request: web.Request, ctx=None) -> web.Response:
    data = cfs.list_providers(modality=request.query.get("modality"))
    return web.json_response({"success": True, "data": {"providers": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def campaigns_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = cfs.list_campaigns()
    return web.json_response({"success": True, "data": {"campaigns": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def campaigns_create_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = cfs.create_campaign(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def campaign_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = cfs.get_campaign(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def campaign_attach_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = cfs.attach_creative(request.match_info["id"], str(body.get("asset_id") or ""))
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def campaign_analytics_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = cfs.campaign_analytics(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def campaign_analytics_post_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        data = cfs.campaign_analytics(request.match_info["id"], body if isinstance(body, dict) else {})
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def media_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = cfs.list_media(modality=request.query.get("modality"))
    return web.json_response({"success": True, "data": {"media": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def media_store_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = cfs.store_media(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def media_generate_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await cfs.media_generate(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def publish_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await cfs.publish(body)
    except KeyError as exc:
        return _error(exc, status=404)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def publish_jobs_handler(request: web.Request, ctx=None) -> web.Response:
    data = cfs.list_publish_jobs()
    return web.json_response({"success": True, "data": {"jobs": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def run_scheduled_handler(request: web.Request, ctx=None) -> web.Response:
    data = cfs.run_scheduled()
    return web.json_response({"success": True, "data": {"published": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_ai_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await cfs.for_ai_runtime(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_multi_agent_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await cfs.for_multi_agent(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_memory_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await cfs.for_project_memory(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_context_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await cfs.for_context_engine(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_workflow_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await cfs.for_workflow(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_event_bus_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await cfs.for_event_bus(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_voice_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await cfs.for_voice(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_skills_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await cfs.for_skills_sdk(body)})


CREATIVE_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", status_handler),
    ("GET", "status", status_handler),
    ("GET", "statistics", statistics_handler),
    ("GET", "analytics", analytics_handler),
    ("GET", "timeline", timeline_handler),
    ("GET", "brands", brands_list_handler),
    ("POST", "brands", brands_upsert_handler),
    ("GET", "brands/{id}", brand_get_handler),
    ("GET", "templates", templates_handler),
    ("GET", "projects", projects_list_handler),
    ("POST", "projects", projects_create_handler),
    ("POST", "generate", generate_handler),
    ("GET", "assets", assets_list_handler),
    ("GET", "assets/{id}", asset_get_handler),
    ("POST", "assets/{id}/review", asset_review_handler),
    ("POST", "assets/{id}/version", asset_version_handler),
    ("GET", "search", search_handler),
    ("POST", "search", search_post_handler),
    ("GET", "providers", providers_handler),
    ("POST", "publish", publish_handler),
    ("GET", "publish/jobs", publish_jobs_handler),
    ("POST", "publish/run-scheduled", run_scheduled_handler),
    ("POST", "integrations/ai-runtime", for_ai_handler),
    ("POST", "integrations/multi-agent", for_multi_agent_handler),
    ("POST", "integrations/project-memory", for_memory_handler),
    ("POST", "integrations/context-engine", for_context_handler),
    ("POST", "integrations/workflow", for_workflow_handler),
    ("POST", "integrations/event-bus", for_event_bus_handler),
    ("POST", "integrations/voice", for_voice_handler),
    ("POST", "integrations/skills-sdk", for_skills_handler),
]

CAMPAIGN_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", campaigns_list_handler),
    ("POST", "", campaigns_create_handler),
    ("GET", "{id}", campaign_get_handler),
    ("POST", "{id}/attach", campaign_attach_handler),
    ("GET", "{id}/analytics", campaign_analytics_handler),
    ("POST", "{id}/analytics", campaign_analytics_post_handler),
]

MEDIA_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", media_list_handler),
    ("GET", "library", media_list_handler),
    ("POST", "", media_store_handler),
    ("POST", "store", media_store_handler),
    ("POST", "generate", media_generate_handler),
    ("GET", "providers", providers_handler),
]


def _mount(app: web.Application, prefix: str, specs: list[tuple[str, str, object]]) -> None:
    for method, rel, handler in specs:
        rel = rel.strip("/")
        path = f"{prefix}/{rel}" if rel else prefix
        add = getattr(app.router, f"add_{method.lower()}")
        add(path, handler)
        # aiohttp treats trailing slash as distinct
        if not rel:
            add(f"{prefix}/", handler)


def register_creative_factory_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=CREATIVE_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/creative",
        legacy_prefix="/management/creative-factory",
    )
    _mount(app, "/api/creative", CREATIVE_ROUTE_SPECS)
    _mount(app, "/api/campaigns", CAMPAIGN_ROUTE_SPECS)
    _mount(app, "/api/media", MEDIA_ROUTE_SPECS)
