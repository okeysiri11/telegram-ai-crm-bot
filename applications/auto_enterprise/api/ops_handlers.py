"""HTTP handlers — Auto Ops private desk (/api/auto-ops/v1) — AUTO 1.0."""

from __future__ import annotations

import os

from aiohttp import web

from applications.auto_enterprise.api.middleware import json_response
from applications.auto_enterprise.config import DEFAULT_CONFIG
from services.auto_ops import get_auto_ops_service


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
        or "auto_manager"
    )


def _actor(request: web.Request) -> str | None:
    return request.headers.get("X-Principal") or request.headers.get("X-User-Id")


def _status(result: dict, *, created: bool = False) -> int:
    if result.get("ok") is True:
        return 201 if created else 200
    err = result.get("error")
    if err == "forbidden":
        return 403
    if err == "not_found":
        return 404
    if err == "conflict":
        return 409
    return 400


async def ops_health_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    db_online = False
    try:
        from database.session import check_db_health

        db_online = bool((await check_db_health()).get("ok"))
    except Exception:
        db_online = False
    env = (os.environ.get("ENVIRONMENT") or "development").strip().lower() or "development"
    telegram = svc.telegram()
    return json_response(
        {
            "status": "ok",
            "ok": True,
            "sprint": DEFAULT_CONFIG.sprint,
            "application_version": DEFAULT_CONFIG.application_version,
            "environment": env,
            "private": True,
            "public": False,
            "database": {"online": db_online, "engine": "postgres"},
            "roles": svc.roles(),
            "telegram": telegram,
        }
    )


async def ops_roles_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    return json_response({"ok": True, "roles": svc.roles()})


async def ops_catalogs_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    denied = await svc.settings(_org(request), _role(request))
    if denied.get("ok") is False:
        return json_response(denied, status=_status(denied))
    return json_response({"ok": True, "catalogs": svc.catalogs()})


async def ops_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    result = await svc.dashboard(_org(request, body), _role(request, body))
    return json_response(result, status=_status(result))


async def ops_vehicles_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        q = {k: str(v) for k, v in request.rel_url.query.items()}
        result = await svc.list_vehicles(org, role, q)
        return json_response(result, status=_status(result))
    result = await svc.create_vehicle(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def ops_vehicle_detail_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    vehicle_id = request.match_info.get("vehicle_id") or ""
    if request.method == "GET":
        result = await svc.get_vehicle(_org(request), vehicle_id, _role(request), _actor(request))
        return json_response(result, status=_status(result))
    body = await _read_json(request)
    result = await svc.update_vehicle(_org(request, body), vehicle_id, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def ops_expenses_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        q = {k: str(v) for k, v in request.rel_url.query.items()}
        result = await svc.list_expenses(org, role, q)
        return json_response(result, status=_status(result))
    result = await svc.create_expense(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def ops_expense_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    expense_id = request.match_info.get("expense_id") or ""
    if request.method == "DELETE":
        result = await svc.delete_expense(_org(request), expense_id, _role(request), _actor(request))
        return json_response(result, status=_status(result))
    body = await _read_json(request)
    result = await svc.update_expense(_org(request, body), expense_id, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def ops_clients_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_clients(org, role)
        return json_response(result, status=_status(result))
    result = await svc.create_client(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def ops_documents_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        q = {k: str(v) for k, v in request.rel_url.query.items()}
        result = await svc.list_documents(org, role, q, _actor(request))
        return json_response(result, status=_status(result))
    result = await svc.create_document(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def ops_document_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    document_id = request.match_info.get("document_id") or ""
    result = await svc.delete_document(_org(request), document_id, _role(request), _actor(request))
    return json_response(result, status=_status(result))


async def ops_photos_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        q = {k: str(v) for k, v in request.rel_url.query.items()}
        result = await svc.list_photos(org, role, q)
        return json_response(result, status=_status(result))
    result = await svc.create_photo(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def ops_photo_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    photo_id = request.match_info.get("photo_id") or ""
    if request.method == "DELETE":
        result = await svc.delete_photo(_org(request), photo_id, _role(request), _actor(request))
        return json_response(result, status=_status(result))
    result = await svc.set_cover_photo(_org(request), photo_id, _role(request))
    return json_response(result, status=_status(result))


async def ops_tasks_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        q = {k: str(v) for k, v in request.rel_url.query.items()}
        result = await svc.list_tasks(org, role, q)
        return json_response(result, status=_status(result))
    result = await svc.create_task(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def ops_task_complete_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    task_id = request.match_info.get("task_id") or ""
    result = await svc.complete_task(_org(request), task_id, _role(request))
    return json_response(result, status=_status(result))


async def ops_audit_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.list_audit(_org(request), _role(request), q)
    return json_response(result, status=_status(result))


async def ops_reports_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.reports(_org(request), _role(request), q)
    return json_response(result, status=_status(result))


async def ops_client_item_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    cid = request.match_info.get("client_id") or ""
    if request.method == "GET":
        result = await svc.get_client(_org(request), cid, _role(request))
        return json_response(result, status=_status(result))
    body = await _read_json(request)
    result = await svc.update_client(_org(request, body), cid, body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result))


async def ops_search_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.search_auto(_org(request), _role(request), q)
    return json_response(result, status=_status(result))


async def ops_document_get_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.get_document_access(_org(request), request.match_info.get("document_id") or "", _role(request), _actor(request))
    return json_response(result, status=_status(result))


async def ops_settings_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.settings(_org(request), _role(request))
    return json_response(result, status=_status(result))


async def ops_telegram_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    denied = await svc.settings(_org(request), _role(request))
    if denied.get("ok") is False:
        return json_response(denied, status=_status(denied))
    return json_response({"ok": True, **svc.telegram()})


async def ops_files_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    org, role = _org(request), _role(request)
    if request.method == "GET":
        result = await svc.list_files(org, role)
        return json_response(result, status=_status(result))
    as_photo = str(request.rel_url.query.get("as_photo") or "").lower() in {"1", "true", "yes"}
    document_type = request.rel_url.query.get("document_type")
    photo_category = request.rel_url.query.get("photo_category")
    ctype = request.headers.get("Content-Type", "")
    if "json" in ctype:
        body = await _read_json(request)
        import base64

        raw = body.get("content_base64") or body.get("content") or ""
        try:
            data = base64.b64decode(raw) if body.get("content_base64") else str(raw).encode("utf-8")
        except Exception:
            data = b""
        result = await svc.upload_file(
            org,
            filename=str(body.get("filename") or "document.bin"),
            mime_type=body.get("mime_type"),
            data=data,
            entity_type=body.get("entity_type"),
            entity_id=body.get("entity_id"),
            role=role,
            uploaded_by=_actor(request),
            as_photo=bool(body.get("as_photo")) or as_photo,
            photo_category=body.get("photo_category") or photo_category,
            document_type=body.get("document_type") or document_type,
        )
        return json_response(result, status=_status(result, created=True))
    reader = await request.multipart()
    filename = "upload.bin"
    mime_type = None
    entity_type = request.rel_url.query.get("entity_type")
    entity_id = request.rel_url.query.get("entity_id")
    chunks: list[bytes] = []
    while True:
        part = await reader.next()
        if part is None:
            break
        name = part.name or ""
        if name == "file":
            filename = part.filename or filename
            mime_type = part.headers.get("Content-Type")
            chunks.append(await part.read())
        elif name == "filename":
            filename = (await part.text()).strip() or filename
        elif name == "entity_type":
            entity_type = await part.text()
        elif name == "entity_id":
            entity_id = await part.text()
        elif name == "as_photo":
            as_photo = (await part.text()).strip().lower() in {"1", "true", "yes"}
        elif name == "photo_category":
            photo_category = await part.text()
        elif name == "document_type":
            document_type = await part.text()
        elif name == "mime_type":
            mime_type = await part.text()
    data = b"".join(chunks)
    if not data:
        return json_response({"ok": False, "error": "validation", "message_ru": "Файл не передан"}, status=400)
    result = await svc.upload_file(
        org,
        filename=filename,
        mime_type=mime_type,
        data=data,
        entity_type=entity_type,
        entity_id=entity_id,
        role=role,
        uploaded_by=_actor(request),
        as_photo=as_photo,
        photo_category=photo_category,
        document_type=document_type,
    )
    return json_response(result, status=_status(result, created=True))


async def ops_file_content_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    file_id = request.match_info.get("file_id") or ""
    err, data = await svc.file_content(_org(request), file_id, _role(request))
    if err:
        return json_response(err, status=_status(err))
    meta = (await svc.list_files(_org(request), _role(request))).get("items") or []
    mime = "application/octet-stream"
    name = file_id
    for item in meta:
        if str(item.get("id")) == file_id:
            mime = str(item.get("mime_type") or mime)
            name = str(item.get("file_name") or name)
            break
    return web.Response(
        body=data or b"",
        content_type=mime,
        headers={"Content-Disposition": f'inline; filename="{name}"', "Cache-Control": "private, no-store"},
    )
