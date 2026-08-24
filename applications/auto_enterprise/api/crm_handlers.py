"""HTTP handlers — Auto Ops CRM / sales / receipts (AUTO 1.3)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_enterprise.api.middleware import json_response
from applications.auto_enterprise.api.ops_handlers import _actor, _org, _read_json, _role, _status
from services.auto_ops import get_auto_ops_service


def _q(request: web.Request) -> dict[str, str]:
    return {k: str(v) for k, v in request.rel_url.query.items()}


async def deals_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_deals(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_deal(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def deal_detail_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    did = request.match_info.get("deal_id") or ""
    if request.method == "GET":
        result = await svc.get_deal(_org(request), did, _role(request))
        return json_response(result, status=_status(result))
    body = await _read_json(request)
    result = await svc.update_deal(_org(request, body), did, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def reservations_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_reservations(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_reservation(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def reservation_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.update_reservation(_org(request, body), request.match_info.get("reservation_id") or "", body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def sales_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_sales(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_sale(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def sale_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.update_sale(_org(request, body), request.match_info.get("sale_id") or "", body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def receipts_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_receipts(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_receipt(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def receipt_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.update_receipt(_org(request, body), request.match_info.get("receipt_id") or "", body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def crm_demo_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.seed_demo_crm(_org(request, body), body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result, created=True))
