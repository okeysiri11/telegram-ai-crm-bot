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
        return 400
    return 201 if created else 200


async def ops_health_handler(_request: web.Request) -> web.Response:
    return json_response(get_recruiting_ops_service().health())


async def ops_roles_handler(_request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    return json_response({"ok": True, "roles": svc.roles()})


async def ops_catalogs_handler(_request: web.Request) -> web.Response:
    return json_response(get_recruiting_ops_service().catalogs())


async def ops_vanguard_contract_handler(_request: web.Request) -> web.Response:
    return json_response(get_recruiting_ops_service().vanguard_contract())


async def ops_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    result = await svc.dashboard(_org(request, body), _role(request, body))
    return json_response(result, status=_status_for(result))


async def ops_analytics_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    result = await svc.analytics(_org(request), _role(request))
    return json_response(result, status=_status_for(result))


async def ops_activity_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    result = await svc.list_activity(_org(request), _role(request))
    return json_response(result, status=_status_for(result))


async def ops_leads_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_kind(org, "lead", role)
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
        result = await svc.list_kind(org, "candidate", role)
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
        result = await svc.list_kind(org, "vacancy", role)
        return json_response(result, status=_status_for(result))
    result = await svc.create_vacancy(org, body, role)
    return json_response(result, status=_status_for(result, created=True))


async def ops_campaigns_handler(request: web.Request) -> web.Response:
    svc = get_recruiting_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_kind(org, "campaign", role)
        return json_response(result, status=_status_for(result))
    result = await svc.create_campaign(org, body, role)
    return json_response(result, status=_status_for(result, created=True))


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
