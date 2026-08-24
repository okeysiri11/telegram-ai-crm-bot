"""HTTP handlers — Auto Ops document OS (AUTO 1.6)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_enterprise.api.middleware import json_response
from applications.auto_enterprise.api.ops_handlers import _actor, _org, _read_json, _role, _status
from services.auto_ops import get_auto_ops_service


def _q(request: web.Request) -> dict[str, str]:
    return {k: str(v) for k, v in request.rel_url.query.items()}


def _file_response(result: dict) -> web.Response:
    raw = result.get("content")
    if result.get("ok") and isinstance(raw, (bytes, bytearray)):
        filename = str(result.get("filename") or "download.bin")
        ctype = str(result.get("content_type") or "application/octet-stream")
        return web.Response(
            body=bytes(raw),
            headers={
                "Content-Type": ctype.split(";")[0],
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    return json_response(result, status=_status(result))


async def documents_desk_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.documents_desk(_org(request), _role(request), _q(request), _actor(request))
    return json_response(result, status=_status(result))


async def documents_packages_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    q = _q(request)
    kind = (q.get("kind") or "sale").strip()
    if kind == "registration":
        result = await svc.registration_package(_org(request), _role(request), q, _actor(request))
    else:
        result = await svc.sale_package(_org(request), _role(request), q, _actor(request))
    return json_response(result, status=_status(result))


async def documents_templates_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_document_templates(org, role, _q(request), _actor(request))
        return json_response(result, status=_status(result))
    result = await svc.save_document_template(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def documents_template_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    tid = request.match_info.get("template_id") or ""
    result = await svc.delete_document_template(_org(request), tid, _role(request), _actor(request))
    return json_response(result, status=_status(result))


async def documents_generate_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.generate_document(_org(request, body), body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result, created=True))


async def documents_export_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.export_documents_csv(_org(request), _role(request), _q(request), _actor(request))
    return _file_response(result)


async def documents_zip_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.zip_vehicle_dossier(_org(request), _role(request), _q(request), _actor(request))
    return _file_response(result)


async def documents_dossiers_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    q = _q(request)
    q["vehicle_id"] = request.match_info.get("vehicle_id") or q.get("vehicle_id") or ""
    result = await svc.document_dossiers(_org(request), _role(request), q, _actor(request))
    return json_response(result, status=_status(result))


async def documents_timeline_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.document_timeline(_org(request), _role(request), _q(request), _actor(request))
    return json_response(result, status=_status(result))


async def documents_status_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    did = request.match_info.get("document_id") or ""
    result = await svc.update_document_status(_org(request, body), did, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def documents_check_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    q = {**_q(request), **{k: str(v) for k, v in body.items() if v is not None and not isinstance(v, (dict, list))}}
    result = await svc.check_document_completeness(_org(request, body), q, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def documents_company_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.save_company_profile(_org(request, body), body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))
