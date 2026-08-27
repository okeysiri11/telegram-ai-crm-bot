"""HTTP handlers — Recruiting Ops (/api/recruiting-ops/v1)."""

from __future__ import annotations

from aiohttp import web

from applications.recruiting_enterprise.api.middleware import json_response
from services.recruiting_ops import get_recruiting_ops_service


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _org(request: web.Request, body: dict | None = None) -> str:
    body = body or {}
    return str(
        body.get("organization_id")
        or body.get("tenant_id")
        or request.rel_url.query.get("organization_id")
        or request.rel_url.query.get("tenant_id")
        or request.headers.get("X-Organization-Id")
        or request.headers.get("X-Tenant-Id")
        or "default"
    )


def _project(request: web.Request) -> str | None:
    raw = request.rel_url.query.get("project") or request.rel_url.query.get("project_key")
    return str(raw).strip() if raw else None


def _role(request: web.Request, body: dict | None = None) -> str:
    body = body or {}
    return str(
        body.get("role")
        or request.rel_url.query.get("role")
        or request.headers.get("X-Role")
        or "recruiter"
    )


def _status_for(result: dict, *, created: bool = False) -> int:
    if result.get("ok") is False:
        err = result.get("error")
        if err == "forbidden":
            return 403
        if err == "not_found":
            return 404
        if err in {"missing_signature", "bad_signature", "expired_signature"}:
            return 401
        if err in {"storage_unavailable", "ingest_not_configured", "store_unavailable"}:
            return 503
        return 400
    if result.get("duplicate"):
        return 200
    return 201 if created else 200


async def ops_health_handler(request: web.Request) -> web.Response:
    import os

    svc = get_recruiting_ops_service()
    await svc.ensure_hydrated(_org(request))
    await svc.ensure_hydrated(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
    return json_response(svc.health())


async def ops_diagnostics_handler(_request: web.Request) -> web.Response:
    result = await get_recruiting_ops_service().infrastructure_diagnostics()
    return json_response(result)


async def ops_tracking_recover_handler(_request: web.Request) -> web.Response:
    result = await get_recruiting_ops_service().recover_tracking_records()
    return json_response(result)


async def ops_roles_handler(_request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    return json_response({"ok": True, "roles": svc.roles()})


async def ops_catalogs_handler(_request: web.Request) -> web.Response:
    return json_response(get_recruiting_ops_service().catalogs())


async def ops_ads_foundation_handler(_request: web.Request) -> web.Response:
    from services.recruiting_ops.ads_foundation import ads_foundation

    return json_response(ads_foundation())


async def ops_vanguard_contract_handler(_request: web.Request) -> web.Response:
    return json_response(get_recruiting_ops_service().vanguard_contract())


async def ops_vanguard_ingest_handler(request: web.Request) -> web.Response:
    import json as json_lib

    from services.recruiting_ops.ingest_auth import verify_ingest_request

    raw = await request.read()
    auth = verify_ingest_request(
        body=raw,
        signature=request.headers.get("X-Vanguard-Signature") or request.headers.get("X-Signature"),
        timestamp=request.headers.get("X-Vanguard-Timestamp") or request.headers.get("X-Timestamp"),
        nonce=request.headers.get("X-Vanguard-Nonce") or request.headers.get("X-Nonce"),
    )
    if not auth.get("ok"):
        return json_response(auth, status=_status_for(auth))
    try:
        body = json_lib.loads(raw.decode("utf-8") or "{}")
        if not isinstance(body, dict):
            body = {}
    except Exception:
        return json_response(
            {"ok": False, "error": "validation", "message_ru": "Некорректный JSON"},
            status=400,
        )
    result = await get_recruiting_ops_service().ingest_vanguard_lead(body)
    return json_response(result, status=_status_for(result, created=not result.get("duplicate")))


async def ops_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    result = await svc.dashboard(_org(request, body), _role(request, body))
    return json_response(result, status=_status_for(result))


async def ops_analytics_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    result = await svc.analytics(_org(request), _role(request), project=_project(request))
    return json_response(result, status=_status_for(result))


async def ops_activity_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    result = await svc.list_activity(_org(request), _role(request), project=_project(request))
    return json_response(result, status=_status_for(result))


async def ops_leads_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_kind(org, "lead", role, project=_project(request))
        return json_response(result, status=_status_for(result))
    result = await svc.create_lead(org, body, role)
    return json_response(result, status=_status_for(result, created=True))


async def ops_lead_assign_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request)
    lead_id = request.match_info.get("lead_id") or ""
    result = await svc.assign_lead(_org(request, body), lead_id, body, _role(request, body))
    return json_response(result, status=_status_for(result))


async def ops_lead_note_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request)
    lead_id = request.match_info.get("lead_id") or ""
    result = await svc.add_note(_org(request, body), lead_id, body, _role(request, body))
    return json_response(result, status=_status_for(result))


async def ops_lead_qualify_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request)
    lead_id = request.match_info.get("lead_id") or ""
    result = await svc.qualify_lead(_org(request, body), lead_id, _role(request, body))
    return json_response(result, status=_status_for(result))


async def ops_lead_convert_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request)
    lead_id = request.match_info.get("lead_id") or ""
    result = await svc.convert_lead(_org(request, body), lead_id, body, _role(request, body))
    return json_response(result, status=_status_for(result, created=True))


async def ops_candidates_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_kind(org, "candidate", role, project=_project(request))
        return json_response(result, status=_status_for(result))
    result = await svc.create_candidate(org, body, role)
    return json_response(result, status=_status_for(result, created=True))


async def ops_candidate_stage_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request)
    candidate_id = request.match_info.get("candidate_id") or ""
    result = await svc.move_candidate(_org(request, body), candidate_id, body, _role(request, body))
    return json_response(result, status=_status_for(result))


async def ops_vacancies_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_kind(org, "vacancy", role, project=_project(request))
        return json_response(result, status=_status_for(result))
    result = await svc.create_vacancy(org, body, role)
    return json_response(result, status=_status_for(result, created=True))


async def ops_campaigns_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_kind(org, "campaign", role, project=_project(request))
        return json_response(result, status=_status_for(result))
    result = await svc.create_campaign(org, body, role)
    return json_response(result, status=_status_for(result, created=True))


async def ops_campaign_update_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request)
    campaign_id = request.match_info.get("campaign_id") or ""
    result = await svc.update_campaign(_org(request, body), campaign_id, body, _role(request, body))
    return json_response(result, status=_status_for(result))


async def ops_ads_control_center_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    project = _project(request) or "vanguard"
    result = await svc.ads_control_center(_org(request), project, _role(request))
    return json_response(result, status=_status_for(result))


async def ops_ads_entities_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request)
    kind = str(body.get("kind") or request.rel_url.query.get("kind") or "")
    result = await svc.upsert_ads_entity(_org(request, body), kind, body, _role(request, body))
    return json_response(result, status=_status_for(result, created=True))


async def ops_tracking_retries_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    result = await svc.process_tracking_retries()
    return json_response(result, status=_status_for(result))


async def ops_tasks_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_kind(org, "task", role)
        return json_response(result, status=_status_for(result))
    result = await svc.create_task(org, body, role)
    return json_response(result, status=_status_for(result, created=True))


async def ops_task_complete_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request)
    task_id = request.match_info.get("task_id") or ""
    result = await svc.complete_task(_org(request, body), task_id, _role(request, body))
    return json_response(result, status=_status_for(result))


async def ops_communications_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_kind(org, "communication", role)
        return json_response(result, status=_status_for(result))
    result = await svc.log_communication(org, body, role)
    return json_response(result, status=_status_for(result, created=True))


async def ops_projects_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    result = await svc.list_projects(_org(request), _role(request))
    return json_response(result, status=_status_for(result))


async def ops_project_overview_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    project_key = request.match_info.get("project_key") or ""
    result = await svc.project_overview(_org(request), project_key, _role(request))
    return json_response(result, status=_status_for(result))


async def ops_project_integration_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    project_key = request.match_info.get("project_key") or ""
    if request.method == "POST":
        result = await svc.check_project_integration(_org(request), project_key, _role(request))
    else:
        result = await svc.project_integration(_org(request), project_key, _role(request))
    return json_response(result, status=_status_for(result))


async def ops_lookup_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    query = str(request.rel_url.query.get("q") or request.rel_url.query.get("external_id") or "")
    result = await svc.lookup_reference(_org(request), query, _role(request))
    return json_response(result, status=_status_for(result))
