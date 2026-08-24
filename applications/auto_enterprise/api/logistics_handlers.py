"""HTTP handlers — Auto Ops logistics desk (AUTO 1.1)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_enterprise.api.middleware import json_response
from applications.auto_enterprise.api.ops_handlers import _actor, _org, _read_json, _role, _status
from services.auto_ops import get_auto_ops_service


def _q(request: web.Request) -> dict[str, str]:
    return {k: str(v) for k, v in request.rel_url.query.items()}


async def logistics_desk_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.list_shipments(_org(request), _role(request), _q(request), _actor(request))
    return json_response(result, status=_status(result))


async def shipments_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_shipments(org, role, _q(request), _actor(request))
        return json_response(result, status=_status(result))
    result = await svc.create_shipment(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def shipment_detail_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    sid = request.match_info.get("shipment_id") or ""
    if request.method == "GET":
        result = await svc.get_shipment(_org(request), sid, _role(request), _actor(request))
        return json_response(result, status=_status(result))
    body = await _read_json(request)
    result = await svc.update_shipment(_org(request, body), sid, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def shipment_events_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    sid = request.match_info.get("shipment_id") or ""
    result = await svc.add_shipment_event(_org(request, body), sid, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result, created=True))


async def carriers_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_carriers(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_carrier(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def carrier_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.update_carrier(_org(request, body), request.match_info.get("carrier_id") or "", body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def drivers_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_drivers(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_driver(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def driver_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.update_driver(_org(request, body), request.match_info.get("driver_id") or "", body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def trucks_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_trucks(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_truck(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def truck_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.update_truck(_org(request, body), request.match_info.get("truck_id") or "", body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def containers_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_containers(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_container(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def container_detail_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    cid = request.match_info.get("container_id") or ""
    if request.method == "GET":
        result = await svc.get_container(_org(request), cid, _role(request))
        return json_response(result, status=_status(result))
    body = await _read_json(request)
    result = await svc.update_container(_org(request, body), cid, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def container_vehicles_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.add_vehicle_to_container(
        _org(request, body),
        request.match_info.get("container_id") or "",
        body,
        _role(request, body),
        _actor(request),
    )
    return json_response(result, status=_status(result, created=True))


async def vessels_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_vessels(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_vessel(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def vessel_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.update_vessel(_org(request, body), request.match_info.get("vessel_id") or "", body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def ports_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_ports(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.create_port(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def notifications_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.list_notifications(_org(request), _role(request))
    return json_response(result, status=_status(result))


async def logistics_settings_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else None
    result = await svc.logistics_settings(_org(request, body or {}), _role(request, body or {}), body)
    return json_response(result, status=_status(result))


async def logistics_demo_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.seed_demo_logistics(_org(request, body), body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result, created=True))


async def document_item_update_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    document_id = request.match_info.get("document_id") or ""
    if request.method == "POST" and request.rel_url.query.get("restore"):
        result = await svc.restore_document(_org(request), document_id, _role(request), _actor(request))
        return json_response(result, status=_status(result))
    body = await _read_json(request)
    if body.get("restore"):
        result = await svc.restore_document(_org(request, body), document_id, _role(request, body), _actor(request))
        return json_response(result, status=_status(result))
    result = await svc.update_document(_org(request, body), document_id, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def logistics_providers_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_logistics_providers(org, role, _q(request))
        return json_response(result, status=_status(result))
    result = await svc.upsert_logistics_provider(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def logistics_provider_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    pid = request.match_info.get("provider_id") or ""
    result = await svc.upsert_logistics_provider(_org(request, body), body, _role(request, body), _actor(request), provider_id=pid)
    return json_response(result, status=_status(result))


async def logistics_provider_check_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    pid = request.match_info.get("provider_id") or ""
    result = await svc.check_logistics_provider(_org(request), pid, _role(request), _actor(request))
    return json_response(result, status=_status(result))


async def shipment_tracking_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    sid = request.match_info.get("shipment_id") or ""
    fetch = request.method == "POST" or str(request.rel_url.query.get("fetch") or "").lower() in {"1", "true", "yes"}
    result = await svc.shipment_tracking(_org(request), sid, _role(request), fetch=fetch)
    return json_response(result, status=_status(result))


async def vehicle_logistics_history_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    vid = request.match_info.get("vehicle_id") or ""
    result = await svc.vehicle_logistics_history(_org(request), vid, _role(request))
    return json_response(result, status=_status(result))
