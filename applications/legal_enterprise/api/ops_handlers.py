"""HTTP handlers — Legal Ops durable CRM (/api/legal-ops/v1) — Sprint 51.0."""

from __future__ import annotations

from aiohttp import web

from applications.legal_enterprise.api.middleware import json_response
from services.legal_ops import get_legal_ops_service


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
        or "lawyer"
    )


async def ops_health_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    return json_response(
        {
            "status": "ok",
            "sprint": "3.6",
            "google_calendar": svc.gcal_status(),
            "integrations": svc.integrations_catalog().get("items"),
            "roles": svc.roles(),
            "ai": svc.ai_catalog(),
            "providers": svc.providers_catalog(),
        }
    )


async def ops_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    result = await svc.dashboard(_org(request, body), _role(request, body))
    return json_response(result, status=200 if result.get("ok") is not False else 403)


async def ops_clients_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        q = {k: str(v) for k, v in request.rel_url.query.items()}
        result = await svc.list_clients(org, role, q)
        return json_response(result, status=200 if result.get("ok") is not False else 403)
    result = await svc.create_client(org, body, role)
    status = 201 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_cases_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_cases(org, role)
        return json_response(result, status=200 if result.get("ok") is not False else 403)
    result = await svc.create_case(org, body, role)
    status = 201 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_case_detail_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    case_id = request.match_info.get("case_id") or ""
    result = await svc.get_case(_org(request), case_id, _role(request))
    status = 200 if result.get("ok") else (404 if result.get("error") == "not_found" else 403)
    return json_response(result, status=status)


async def ops_contracts_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_contracts(org, role)
        return json_response(result, status=200 if result.get("ok") is not False else 403)
    result = await svc.create_contract(org, body, role)
    status = 201 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_contract_update_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    contract_id = request.match_info.get("contract_id") or body.get("contract_id") or ""
    result = await svc.update_contract(_org(request, body), str(contract_id), body, _role(request, body))
    status = 200 if result.get("ok") else (404 if result.get("error") == "not_found" else 403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_documents_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_documents(org, role)
        return json_response(result, status=200 if result.get("ok") is not False else 403)
    result = await svc.create_document(org, body, role)
    status = 201 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_tasks_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_tasks(org, role)
        return json_response(result, status=200 if result.get("ok") is not False else 403)
    result = await svc.create_task(org, body, role)
    status = 201 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_task_complete_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    task_id = request.match_info.get("task_id") or body.get("task_id") or ""
    result = await svc.complete_task(_org(request, body), str(task_id), _role(request, body))
    status = 200 if result.get("ok") else (404 if result.get("error") == "not_found" else 403)
    return json_response(result, status=status)


async def ops_hearings_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_hearings(org, role)
        return json_response(result, status=200 if result.get("ok") is not False else 403)
    result = await svc.create_hearing(org, body, role)
    status = 201 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_calendar_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_calendar(org, role)
        return json_response(result, status=200 if result.get("ok") is not False else 403)
    result = await svc.create_calendar_event(org, body, role)
    status = 201 if result.get("ok") else (409 if result.get("error") == "duplicate" else 403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_calendar_sync_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    event_id = str(body.get("event_id") or request.match_info.get("event_id") or "")
    result = await svc.sync_calendar(_org(request, body), event_id, _role(request, body))
    status = 200 if result.get("ok") else (409 if result.get("error") == "duplicate" else 400)
    return json_response(result, status=status)


async def ops_gcal_status_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    return json_response({"ok": True, **svc.gcal_status()})


async def ops_activity_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    result = await svc.list_activity(
        _org(request),
        entity_type=request.rel_url.query.get("entity_type"),
        entity_id=request.rel_url.query.get("entity_id"),
        role=_role(request),
    )
    return json_response(result, status=200 if result.get("ok") is not False else 403)


async def ops_ai_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    result = await svc.ai_analyze(_org(request, body), body, _role(request, body))
    status = 200 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_ai_catalog_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    return json_response(svc.ai_catalog())


async def ops_ai_context_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    await svc.ensure_hydrated(org)
    q = request.rel_url.query
    exclude = body.get("exclude_sources") if isinstance(body.get("exclude_sources"), list) else []
    if q.get("exclude"):
        exclude = [x.strip() for x in str(q.get("exclude")).split(",") if x.strip()]
    doc_ids = body.get("document_ids")
    if q.get("document_ids"):
        doc_ids = [x.strip() for x in str(q.get("document_ids")).split(",") if x.strip()]
    result = svc.build_context_pack(
        org,
        client_id=body.get("client_id") or q.get("client_id"),
        case_id=body.get("case_id") or q.get("case_id"),
        document_ids=doc_ids if isinstance(doc_ids, list) else None,
        contract_id=body.get("contract_id") or q.get("contract_id"),
        hearing_id=body.get("hearing_id") or q.get("hearing_id"),
        change_id=body.get("change_id") or q.get("change_id"),
        exclude=[str(x) for x in exclude],
        role=role,
    )
    return json_response(result, status=200 if result.get("ok") is not False else 403)


async def ops_ai_analyses_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    org, role = _org(request), _role(request)
    result = await svc.list_ai_analyses(
        org,
        role,
        case_id=request.rel_url.query.get("case_id"),
        include_archived=request.rel_url.query.get("include_archived") == "1",
    )
    return json_response(result, status=200 if result.get("ok") is not False else 403)


async def ops_ai_analysis_detail_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    analysis_id = request.match_info.get("analysis_id") or ""
    result = await svc.get_ai_analysis(_org(request), analysis_id, _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_ai_analysis_archive_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    analysis_id = request.match_info.get("analysis_id") or ""
    result = await svc.archive_ai_analysis(
        _org(request, body), analysis_id, _role(request, body), reason=body.get("archive_reason")
    )
    return json_response(result, status=_kind_status(result))


async def ops_ai_analysis_action_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    analysis_id = request.match_info.get("analysis_id") or ""
    result = await svc.ai_analysis_action(_org(request, body), analysis_id, body, _role(request, body))
    status = 200 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_ai_lawyer_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    result = await svc.ai_lawyer_run(_org(request, body), body, _role(request, body))
    status = 200 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_ai_draft_update_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    document_id = request.match_info.get("document_id") or ""
    result = await svc.update_ai_draft(_org(request, body), document_id, body, _role(request, body))
    status = 200 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_ai_draft_regen_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    document_id = request.match_info.get("document_id") or ""
    result = await svc.regenerate_draft_fragment(_org(request, body), document_id, body, _role(request, body))
    status = 200 if result.get("ok") else (403 if result.get("error") == "forbidden" else 400)
    return json_response(result, status=status)


async def ops_roles_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    return json_response({"ok": True, "items": svc.roles()})


def _kind_status(result: dict, created: bool = False) -> int:
    if result.get("ok"):
        return 201 if created else 200
    err = result.get("error")
    if err == "forbidden":
        return 403
    if err == "not_found":
        return 404
    if err == "duplicate":
        return 409
    return 400


async def ops_entity_get_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    kind = request.match_info.get("kind") or ""
    item_id = request.match_info.get("item_id") or ""
    result = await svc.get_entity(_org(request), kind, item_id, _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_related_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    kind = request.match_info.get("kind") or ""
    item_id = request.match_info.get("item_id") or ""
    result = await svc.related_bundle(_org(request), kind, item_id, _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_entity_update_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    kind = request.match_info.get("kind") or ""
    item_id = request.match_info.get("item_id") or ""
    result = await svc.update_entity(_org(request, body), kind, item_id, body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_entity_archive_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    kind = request.match_info.get("kind") or ""
    item_id = request.match_info.get("item_id") or ""
    result = await svc.archive_entity(
        _org(request, body), kind, item_id, _role(request, body), reason=body.get("archive_reason")
    )
    return json_response(result, status=_kind_status(result))


async def ops_entity_restore_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    kind = request.match_info.get("kind") or ""
    item_id = request.match_info.get("item_id") or ""
    result = await svc.restore_entity(_org(request, body), kind, item_id, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_archive_list_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    result = await svc.list_archive(_org(request), _role(request), request.rel_url.query.get("kind"))
    return json_response(result, status=_kind_status(result))


async def ops_files_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    org, role = _org(request), _role(request)
    if request.method == "GET":
        result = await svc.list_files(
            org,
            role,
            entity_type=request.rel_url.query.get("entity_type"),
            entity_id=request.rel_url.query.get("entity_id"),
            inbox_status=request.rel_url.query.get("inbox_status"),
        )
        return json_response(result, status=_kind_status(result))
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
            description=body.get("description"),
            role=role,
            uploaded_by=role,
        )
        return json_response(result, status=_kind_status(result, created=True))
    reader = await request.multipart()
    filename = "upload.bin"
    mime_type = None
    description = None
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
        elif name == "description":
            description = await part.text()
        elif name == "entity_type":
            entity_type = await part.text()
        elif name == "entity_id":
            entity_id = await part.text()
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
        description=description,
        role=role,
        uploaded_by=role,
    )
    return json_response(result, status=_kind_status(result, created=True))


async def ops_file_replace_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    file_id = request.match_info.get("file_id") or ""
    reader = await request.multipart()
    filename = "upload.bin"
    mime_type = None
    chunks: list[bytes] = []
    while True:
        part = await reader.next()
        if part is None:
            break
        if (part.name or "") == "file":
            filename = part.filename or filename
            mime_type = part.headers.get("Content-Type")
            chunks.append(await part.read())
    result = await svc.replace_file(_org(request), file_id, filename, mime_type, b"".join(chunks), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_file_link_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    file_id = request.match_info.get("file_id") or ""
    result = await svc.link_file(
        _org(request, body),
        file_id,
        str(body.get("entity_type") or ""),
        str(body.get("entity_id") or ""),
        _role(request, body),
    )
    return json_response(result, status=_kind_status(result))


async def ops_file_rename_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    file_id = request.match_info.get("file_id") or ""
    result = await svc.rename_file(_org(request, body), file_id, str(body.get("filename") or ""), _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_file_content_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    file_id = request.match_info.get("file_id") or ""
    meta, data = await svc.file_bytes(_org(request), file_id, _role(request))
    if data is None:
        return json_response(meta or {"ok": False, "error": "not_found"}, status=404)
    return web.Response(
        body=data,
        content_type=str((meta or {}).get("mime_type") or "application/octet-stream"),
        headers={"Content-Disposition": f'inline; filename="{(meta or {}).get("filename") or "file"}"'},
    )


async def ops_inbox_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    result = await svc.list_inbox(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_integrations_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    return json_response(svc.integrations_catalog())


async def ops_gcal_connect_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    st = svc.gcal_status()
    if st.get("status") == "connected":
        return json_response({"ok": True, **st})
    if st.get("oauth_client_configured"):
        return json_response(
            {
                "ok": False,
                "status": st.get("status"),
                "message_ru": st.get("message_ru"),
                "oauth_url": st.get("oauth_url"),
            },
            status=409,
        )
    return json_response(
        {"ok": False, "status": "needs_config", "message_ru": "Требуется настройка Google OAuth"},
        status=409,
    )


async def ops_gcal_callback_handler(request: web.Request) -> web.Response:
    from services.legal_ops import google_calendar as gcal

    code = request.rel_url.query.get("code") or ""
    state = request.rel_url.query.get("state") or ""
    org = _org(request)
    # Basic OAuth state: optional org in state; reject absolute foreign redirects
    if state and ("://" in state or ".." in state):
        return json_response({"ok": False, "message_ru": "Некорректный OAuth state"}, status=400)
    if not code:
        return json_response({"ok": False, "message_ru": "Нет code в callback"}, status=400)
    result = gcal.exchange_oauth_code(code, organization_id=org)
    if result.get("ok"):
        svc = get_legal_ops_service()
        await svc._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="integration",
            entity_id="google_calendar",
            action="GOOGLE_CONNECTED",
            summary="Google Calendar OAuth завершён",
            role=_role(request),
            payload={"mode": result.get("mode")},
        )
    status = 200 if result.get("ok") else 400
    # never echo tokens
    safe = {k: v for k, v in result.items() if "token" not in k.lower() and "secret" not in k.lower()}
    return json_response(safe, status=status)


async def ops_gcal_disconnect_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    result = await svc.disconnect_google(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_integrations_health_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    result = await svc.integration_health(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_providers_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    return json_response(svc.providers_catalog())


async def ops_watchlist_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_watchlist(org, role)
        return json_response(result, status=200 if result.get("ok") is not False else 403)
    result = await svc.add_watchlist(org, body, role)
    return json_response(result, status=_kind_status(result, created=True))


async def ops_watchlist_update_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    wid = request.match_info.get("watchlist_id") or ""
    result = await svc.update_watchlist(_org(request, body), wid, body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_watchlist_check_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    wid = request.match_info.get("watchlist_id") or ""
    result = await svc.check_watchlist_item(_org(request, body), wid, body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_monitor_changes_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    result = await svc.list_monitor_changes(
        _org(request),
        _role(request),
        unread_only=request.rel_url.query.get("unread") == "1",
    )
    return json_response(result, status=200 if result.get("ok") is not False else 403)


async def ops_monitor_change_action_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    cid = request.match_info.get("change_id") or ""
    result = await svc.monitor_change_action(_org(request, body), cid, body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_enforcement_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_enforcement(org, role)
        return json_response(result, status=200 if result.get("ok") is not False else 403)
    result = await svc.create_enforcement(org, body, role)
    return json_response(result, status=_kind_status(result, created=True))


async def ops_enforcement_update_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    eid = request.match_info.get("enforcement_id") or ""
    result = await svc.update_enforcement(_org(request, body), eid, body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_notifications_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    result = await svc.list_notifications(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_monitor_settings_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.get_monitor_settings(org, role)
        return json_response(result, status=_kind_status(result))
    result = await svc.update_monitor_settings(org, body, role)
    return json_response(result, status=_kind_status(result))


async def ops_calendar_sync_mapped_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    event_id = request.match_info.get("event_id") or body.get("event_id") or ""
    result = await svc.sync_event_with_mapping(_org(request, body), str(event_id), _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_reminders_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    result = await svc.list_reminders(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_case_update_handler(request: web.Request) -> web.Response:
    svc = get_legal_ops_service()
    body = await _read_json(request)
    case_id = request.match_info.get("case_id") or ""
    result = await svc.update_entity(_org(request, body), "case", case_id, body, _role(request, body))
    return json_response(result, status=_kind_status(result))

