"""HTTP handlers — Auto Ops customs desk (AUTO 1.2)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_enterprise.api.middleware import json_response
from applications.auto_enterprise.api.ops_handlers import _actor, _org, _read_json, _role, _status
from services.auto_ops import get_auto_ops_service


def _q(request: web.Request) -> dict[str, str]:
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    ws = request.headers.get("X-Workspace-Id")
    if ws and "workspace_id" not in q:
        q["workspace_id"] = ws
    return q


async def customs_desk_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.list_customs_cases(_org(request), _role(request), _q(request))
    return json_response(result, status=_status(result))


async def cases_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_customs_cases(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_customs_case(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def case_detail_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    cid = request.match_info.get("case_id") or ""
    if request.method == "GET":
        result = await svc.get_customs_case(_org(request), cid, _role(request), _q(request))
        return json_response(result, status=_status(result))
    body = await _read_json(request)
    result = await svc.update_customs_case(_org(request, body), cid, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def case_calculate_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    cid = request.match_info.get("case_id") or ""
    result = await svc.calculate_customs_case(_org(request, body), cid, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def brokers_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_brokers(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_broker(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def broker_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.update_broker(_org(request, body), request.match_info.get("broker_id") or "", body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def customs_settings_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else None
    result = await svc.customs_settings(_org(request, body or {}), _role(request, body or {}), body)
    return json_response(result, status=_status(result))


async def customs_demo_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.seed_demo_customs(_org(request, body), body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result, created=True))


async def case_summary_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    cid = request.match_info.get("case_id") or ""
    result = await svc.get_customs_summary(_org(request), cid, _role(request), _q(request))
    return json_response(result, status=_status(result))


async def case_payments_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    cid = request.match_info.get("case_id") or ""
    result = await svc.add_customs_payment(_org(request, body), cid, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result, created=True))


async def case_payment_confirm_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    cid = request.match_info.get("case_id") or ""
    eid = request.match_info.get("expense_id") or ""
    result = await svc.confirm_customs_payment(_org(request, body), cid, eid, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))
