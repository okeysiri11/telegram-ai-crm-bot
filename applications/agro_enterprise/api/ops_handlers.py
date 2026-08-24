"""HTTP handlers — AGRO Ops durable desk (/api/agro-ops/v1) — Production 1.0."""

from __future__ import annotations

import base64

from aiohttp import web

from applications.agro_enterprise.api.middleware import json_response
from services.agro_ops import get_agro_ops_service
from services.agro_ops.intelligence import AGENTS, MARKET_GROUPS, PROVIDER_CATALOG, REPORT_SECTIONS
from services.agro_ops.providers import HEALTH_COLORS


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
        or "agro_manager"
    )


def _workspace(request: web.Request, body: dict | None = None) -> str:
    body = body or {}
    return str(
        body.get("workspace_id")
        or request.rel_url.query.get("workspace_id")
        or request.headers.get("X-Workspace-Id")
        or "agro"
    ).strip() or "agro"


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


async def ops_health_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    return json_response(
        {
            "status": "ok",
            "sprint": "agro-2.0",
            "pipeline_version": "AGRO_1_9",
            "ux_version": "AGRO_2_0",
            "roles": svc.roles(),
            "catalogs": svc.catalogs(),
            "providers": PROVIDER_CATALOG,
            "report_sections": [{"id": i, "label_ru": l} for i, l in REPORT_SECTIONS],
            "market_groups": MARKET_GROUPS,
            "agents": [{"id": i, "label_ru": l, "scope_ru": s} for i, l, s in AGENTS],
            "channels": svc.notification_channels(),
            "health_colors": HEALTH_COLORS,
            "gap_severities": ["CRITICAL", "IMPORTANT", "OPTIONAL"],
            "command_center": "AGRO_2_0",
            "crm_version": "AGRO_2_1",
            "ops_version": "AGRO_2_2",
            "production_version": "AGRO_2_6",
            "audit_version": "AGRO_2_5",
        }
    )


async def ops_roles_handler(request: web.Request) -> web.Response:
    return json_response({"ok": True, "items": get_agro_ops_service().roles()})


async def ops_catalogs_handler(request: web.Request) -> web.Response:
    return json_response(get_agro_ops_service().catalogs())


async def ops_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    result = await svc.dashboard(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_command_center_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    q.setdefault("workspace_id", _workspace(request))
    result = await svc.command_center_read(_org(request), _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_management_report_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    q.setdefault("workspace_id", _workspace(request))
    result = await svc.management_brief(_org(request), _role(request), q)
    if not result.get("ok"):
        return json_response(result, status=_kind_status(result))
    want_html = (request.rel_url.query.get("format") or "").lower() in {"html", "print"} or "text/html" in request.headers.get("Accept", "")
    if want_html:
        return web.Response(
            text=str(result.get("html") or ""),
            content_type="text/html",
            charset="utf-8",
            headers={"Content-Disposition": 'inline; filename="agro_management_brief.html"'},
        )
    return json_response(result)


def _actor(request: web.Request, body: dict | None = None) -> str:
    body = body or {}
    return str(body.get("actor") or body.get("actor_id") or request.rel_url.query.get("actor") or request.headers.get("X-Actor") or "")


async def ops_crm_list_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    if _actor(request) and "actor" not in q:
        q["actor"] = _actor(request)
    result = await svc.crm_list(_org(request), _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_crm_counterparty_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.counterparty_360(_org(request), request.match_info.get("item_id") or "", _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_crm_deal_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.deal_360(_org(request), request.match_info.get("item_id") or "", _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_crm_deal_status_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.set_deal_status(_org(request, body), request.match_info.get("item_id") or "", body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_crm_duplicates_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.crm_duplicates(_org(request), _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_crm_import_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.import_counterparties(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_crm_export_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.export_crm(_org(request), _role(request), q)
    if result.get("ok") and str(q.get("format") or "") == "csv":
        return web.Response(
            text=str(result.get("csv") or ""),
            content_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="agro_crm.csv"'},
        )
    return json_response(result, status=_kind_status(result))


async def ops_crm_communication_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.add_communication(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_crm_note_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.add_note(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_crm_followup_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.create_follow_up(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_crm_analytics_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.crm_analytics(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_operations_list_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    if request.method == "POST":
        body = await _read_json(request)
        result = await svc.create_operation(_org(request, body), body, _role(request, body))
        return json_response(result, status=_kind_status(result, created=True))
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.list_operations(_org(request), _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_operations_today_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.grain_today(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_operations_stock_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.grain_stock(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_operations_fifo_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.fifo_suggest(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_operation_get_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.operation_360(_org(request), request.match_info.get("item_id") or "", _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_operation_status_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.set_operation_status(_org(request, body), request.match_info.get("item_id") or "", body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_operation_weighing_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    body.setdefault("operation_id", request.match_info.get("item_id"))
    result = await svc.add_weighing(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_operation_quality_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    body.setdefault("operation_id", request.match_info.get("item_id"))
    result = await svc.add_quality_test(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_operation_quality_decision_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.quality_decision(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_operation_receive_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    body.setdefault("operation_id", request.match_info.get("item_id"))
    result = await svc.receive_operation(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_operation_process_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    body.setdefault("operation_id", request.match_info.get("item_id"))
    result = await svc.process_operation(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_operation_allocate_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    body.setdefault("operation_id", request.match_info.get("item_id"))
    result = await svc.allocate_sale(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_operation_expense_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    body.setdefault("operation_id", request.match_info.get("item_id"))
    result = await svc.add_expense(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_operation_truck_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    body.setdefault("operation_id", request.match_info.get("item_id"))
    result = await svc.add_truck_run(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_operation_transfer_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    body.setdefault("operation_id", request.match_info.get("item_id"))
    result = await svc.transfer_lot(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_truck_status_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.set_truck_status(_org(request, body), request.match_info.get("item_id") or "", body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_exception_status_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.set_exception_status(_org(request, body), request.match_info.get("item_id") or "", body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_search_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = str(request.rel_url.query.get("q") or request.rel_url.query.get("query") or "")
    result = await svc.search_ops(_org(request), _role(request), q)
    return json_response(result, status=_kind_status(result))


KIND_ALIASES = {
    "counterparties": "counterparty",
    "contacts": "contact",
    "crops": "crop",
    "deals": "deal",
    "contracts": "contract",
    "documents": "document",
    "calculations": "calculation",
    "invoices": "invoice",
    "payments": "payment",
    "shipments": "shipment",
    "warehouses": "warehouse",
    "tasks": "task",
    "calendar": "calendar",
    "markets": "market",
    "notifications": "notification",
    "activity": "activity",
    "settings": "settings",
    "carriers": "carrier",
    "vehicles": "vehicle",
    "trailers": "trailer",
    "drivers": "driver",
    "trips": "trip",
    "market-prices": "market_price",
    "market_prices": "market_price",
    "storage-units": "storage_unit",
    "lots": "inventory_lot",
    "inventory-lots": "inventory_lot",
    "warehouse-operations": "warehouse_operation",
    "availabilities": "availability",
    "demands": "demand",
    "alert-rules": "alert_rule",
    "alerts": "alert",
    "deliveries": "shipment",
    "delivery-legs": "delivery_leg",
    "communications": "communication",
    "notes": "note",
    "bank-accounts": "bank_account",
    "bank_accounts": "bank_account",
    "fields": "agro_field",
    "machines": "machine",
    "implements": "implement",
    "materials": "material",
    "seasons": "crop_season",
    "works": "field_work",
}


async def ops_list_create_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    raw = request.match_info.get("kind") or request.match_info.get("alias") or ""
    kind = KIND_ALIASES.get(raw, raw)
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        q = {k: str(v) for k, v in request.rel_url.query.items()}
        result = await svc.list_entities(org, kind, role, q)
        return json_response(result, status=_kind_status(result))
    result = await svc.create_entity(org, kind, body, role)
    return json_response(result, status=_kind_status(result, created=True))


async def ops_entity_get_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    kind = request.match_info.get("kind") or ""
    item_id = request.match_info.get("item_id") or ""
    result = await svc.get_entity(_org(request), kind, item_id, _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_related_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.related_bundle(
        _org(request),
        request.match_info.get("kind") or "",
        request.match_info.get("item_id") or "",
        _role(request),
    )
    return json_response(result, status=_kind_status(result))


async def ops_entity_update_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.update_entity(
        _org(request, body),
        request.match_info.get("kind") or "",
        request.match_info.get("item_id") or "",
        body,
        _role(request, body),
    )
    return json_response(result, status=_kind_status(result))


async def ops_entity_archive_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.archive_entity(
        _org(request, body),
        request.match_info.get("kind") or "",
        request.match_info.get("item_id") or "",
        body,
        _role(request, body),
    )
    return json_response(result, status=_kind_status(result))


async def ops_entity_restore_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.restore_entity(
        _org(request),
        request.match_info.get("kind") or "",
        request.match_info.get("item_id") or "",
        _role(request),
    )
    return json_response(result, status=_kind_status(result))


async def ops_finance_summary_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.finance_summary(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_calc_preview_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.preview_calculation(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_export_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    section = request.match_info.get("section") or request.rel_url.query.get("section") or "invoices"
    result = await svc.export_accounting_csv(_org(request), section, _role(request))
    if not result.get("ok"):
        return json_response(result, status=_kind_status(result))
    filename = str(result.get("filename") or "agro.csv")
    ctype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if filename.endswith(".xlsx") else "text/csv"
    return web.Response(
        text=str(result.get("content") or ""),
        content_type=ctype,
        charset="utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def ops_providers_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.providers_status(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_providers_custom_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.add_custom_source(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_scheduler_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    if request.method == "GET":
        result = await svc.get_scheduler(_org(request), _role(request))
        return json_response(result, status=_kind_status(result))
    body = await _read_json(request)
    result = await svc.put_scheduler(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_intel_import_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.import_intel_item(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_report_generate_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    kind = str(body.get("kind") or request.match_info.get("kind") or "morning")
    if body.get("open_latest") and not body.get("force") and not body.get("generate") and not body.get("recalculate"):
        result = await svc.latest_or_generate(_org(request, body), kind, _role(request, body), generate=False)
        return json_response(result, status=_kind_status(result))
    result = await svc.generate_report(
        _org(request, body), kind, _role(request, body), force=bool(body.get("force") or body.get("generate") or body.get("recalculate"))
    )
    return json_response(result, status=_kind_status(result))


async def ops_reports_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.list_reports(_org(request), _role(request), request.rel_url.query.get("kind"), q)
    return json_response(result, status=_kind_status(result))


async def ops_report_get_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.get_report(_org(request), request.match_info.get("report_id") or "", _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_agents_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    if request.method == "GET":
        result = await svc.list_agent_runs(_org(request), _role(request))
        return json_response(result, status=_kind_status(result))
    body = await _read_json(request)
    result = await svc.run_agents(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_analytics_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.analytics_dashboard(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_analytics_list_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    if request.method == "GET":
        result = await svc.list_analyses(_org(request), _role(request))
        return json_response(result, status=_kind_status(result))
    body = await _read_json(request)
    result = await svc.run_analysis(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_analytics_get_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.get_analysis(_org(request), request.match_info.get("analysis_id") or "", _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_analytics_notify_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.analysis_create_notification(
        _org(request, body), request.match_info.get("analysis_id") or "", body, _role(request, body)
    )
    return json_response(result, status=_kind_status(result, created=True))


async def ops_analytics_task_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.analysis_create_task(
        _org(request, body), request.match_info.get("analysis_id") or "", body, _role(request, body)
    )
    return json_response(result, status=_kind_status(result, created=True))


async def ops_analytics_calendar_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.analysis_create_calendar(
        _org(request, body), request.match_info.get("analysis_id") or "", body, _role(request, body)
    )
    return json_response(result, status=_kind_status(result, created=True))


async def ops_pipeline_rebuild_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.rebuild_after_fix(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_weather_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    crop = request.query.get("crop")
    result = await svc.weather_overview(_org(request), _role(request), crop=crop)
    return json_response(result, status=_kind_status(result))


async def ops_weather_overview_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.weather_overview(_org(request), _role(request), crop=request.query.get("crop"))
    return json_response(result, status=_kind_status(result))


async def ops_weather_regions_index_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.weather_regions_index(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_weather_region_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.weather_oblast(_org(request), request.match_info.get("oblast_id") or "", _role(request), crop=request.query.get("crop"))
    return json_response(result, status=_kind_status(result))


async def ops_weather_forecast_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    try:
        days = int(request.query.get("days") or 7)
    except ValueError:
        days = 7
    result = await svc.weather_forecast(_org(request), _role(request), region=request.query.get("region"), days=days)
    return json_response(result, status=_kind_status(result))


async def ops_weather_outlook_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    try:
        days = int(request.query.get("days") or 30)
    except ValueError:
        days = 30
    result = await svc.weather_outlook(_org(request), _role(request), region=request.query.get("region"), days=days)
    return json_response(result, status=_kind_status(result))


async def ops_weather_agro_risk_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.weather_agro_risk(_org(request), _role(request), region=request.query.get("region"), crop=request.query.get("crop"))
    return json_response(result, status=_kind_status(result))


async def ops_weather_recommendations_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.weather_recommendations(_org(request), _role(request), region=request.query.get("region"), crop=request.query.get("crop"))
    return json_response(result, status=_kind_status(result))


async def ops_weather_refresh_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.weather_refresh(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_desk_settings_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    if request.method == "GET":
        result = await svc.get_desk_settings(_org(request), _role(request))
        return json_response(result, status=_kind_status(result))
    body = await _read_json(request)
    result = await svc.put_desk_settings(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_provider_detail_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.provider_detail(_org(request), request.match_info.get("provider_id") or "", _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_providers_refresh_all_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.refresh_all_providers(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_ask_ai_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.ask_ai(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_channels_handler(request: web.Request) -> web.Response:
    return json_response({"ok": True, "channels": get_agro_ops_service().notification_channels()})


async def ops_files_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    org, role = _org(request), _role(request)
    if request.method == "GET":
        q = {k: str(v) for k, v in request.rel_url.query.items()}
        result = await svc.list_entities(org, "file", role, q)
        return json_response(result, status=_kind_status(result))
    ctype = request.headers.get("Content-Type", "")
    if "json" in ctype:
        body = await _read_json(request)
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
            doc_type=body.get("doc_type"),
            title=body.get("title"),
            issue_date=body.get("issue_date"),
            expiry_date=body.get("expiry_date"),
            comments=body.get("comments"),
            tags=body.get("tags"),
            role=role,
            actor_id=body.get("actor_id"),
        )
        return json_response(result, status=_kind_status(result, created=True))
    reader = await request.multipart()
    filename = "upload.bin"
    mime_type = None
    entity_type = request.rel_url.query.get("entity_type")
    entity_id = request.rel_url.query.get("entity_id")
    doc_type = None
    title = None
    issue_date = None
    expiry_date = None
    comments = None
    tags = None
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
        elif name == "doc_type":
            doc_type = await part.text()
        elif name == "title":
            title = await part.text()
        elif name == "issue_date":
            issue_date = await part.text()
        elif name == "expiry_date":
            expiry_date = await part.text()
        elif name == "comments":
            comments = await part.text()
        elif name == "tags":
            tags = await part.text()
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
        doc_type=doc_type,
        title=title,
        issue_date=issue_date,
        expiry_date=expiry_date,
        comments=comments,
        tags=tags,
        role=role,
    )
    return json_response(result, status=_kind_status(result, created=True))


async def ops_file_content_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    file_id = request.match_info.get("file_id") or ""
    result = await svc.file_content(_org(request), file_id, _role(request))
    if not result.get("ok"):
        return json_response(result, status=_kind_status(result))
    item = result["item"]
    return web.Response(
        body=result["data"],
        content_type=str(item.get("mime_type") or "application/octet-stream"),
        headers={"Content-Disposition": f'inline; filename="{item.get("filename") or "file"}"'},
    )


async def ops_file_rename_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.rename_file(
        _org(request, body),
        request.match_info.get("file_id") or "",
        str(body.get("filename") or body.get("title") or ""),
        _role(request, body),
    )
    return json_response(result, status=_kind_status(result))


async def ops_file_link_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.relink_file(
        _org(request, body),
        request.match_info.get("file_id") or "",
        str(body.get("entity_type") or ""),
        str(body.get("entity_id") or ""),
        _role(request, body),
    )
    return json_response(result, status=_kind_status(result))


async def ops_provider_probe_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.probe_provider(
        _org(request, body),
        request.match_info.get("provider_id") or "",
        _role(request, body),
    )
    return json_response(result, status=_kind_status(result))


async def ops_providers_ingest_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.ingest_providers(
        _org(request, body),
        _role(request, body),
        cadence=body.get("cadence") or request.rel_url.query.get("cadence"),
    )
    return json_response(result, status=_kind_status(result))


async def ops_provider_observations_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.provider_observations(_org(request), _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_logistics_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.logistics_dashboard(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_markets_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.market_dashboard(_org(request), _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_markets_history_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    q = {k: str(v) for k, v in request.rel_url.query.items()}
    result = await svc.price_history(_org(request), _role(request), q)
    return json_response(result, status=_kind_status(result))


async def ops_markets_compare_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.compare_markets(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_landed_cost_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.landed_cost(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_warehouse_dashboard_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.warehouse_dashboard(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_warehouse_operation_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.warehouse_operation(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_warehouse_receive_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.receive_from_trip(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_crop_directory_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.crop_directory(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_crop_balance_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    result = await svc.crop_balance(_org(request), request.match_info.get("item_id") or "", _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_delivery_progress_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.record_delivery_progress(
        _org(request, body),
        request.match_info.get("item_id") or "",
        body,
        _role(request, body),
    )
    return json_response(result, status=_kind_status(result, created=True))


async def ops_alerts_evaluate_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.evaluate_alerts(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_reminders_evaluate_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.evaluate_reminders(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result))


async def ops_calendar_remind_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.set_calendar_reminder(
        _org(request, body),
        request.match_info.get("item_id") or "",
        body,
        _role(request, body),
    )
    return json_response(result, status=_kind_status(result))


async def ops_notification_action_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.notification_action(
        _org(request, body),
        request.match_info.get("item_id") or "",
        body,
        _role(request, body),
    )
    return json_response(result, status=_kind_status(result))


async def ops_task_from_entity_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.create_task_from_entity(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_bootstrap_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.bootstrap_demo(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result, created=not result.get("already")))


async def ops_warehouse_issue_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request)
    result = await svc.issue_to_trip(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


def _q(request: web.Request) -> dict[str, str]:
    return {k: str(v) for k, v in request.rel_url.query.items()}


async def ops_fields_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_fields(org, role, _q(request))
        return json_response(result, status=_kind_status(result))
    result = await svc.create_field(org, body, role)
    return json_response(result, status=_kind_status(result, created=True))


async def ops_fields_map_handler(request: web.Request) -> web.Response:
    result = await get_agro_ops_service().field_map(_org(request), _role(request), _q(request))
    return json_response(result, status=_kind_status(result))


async def ops_fields_today_handler(request: web.Request) -> web.Response:
    result = await get_agro_ops_service().agronomist_today(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_fields_director_handler(request: web.Request) -> web.Response:
    result = await get_agro_ops_service().director_production(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_crop_structure_handler(request: web.Request) -> web.Response:
    result = await get_agro_ops_service().crop_structure(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))


async def ops_crop_costs_handler(request: web.Request) -> web.Response:
    result = await get_agro_ops_service().crop_costs(_org(request), _role(request), _q(request))
    return json_response(result, status=_kind_status(result))


async def ops_field_360_handler(request: web.Request) -> web.Response:
    result = await get_agro_ops_service().field_360(
        _org(request), request.match_info.get("item_id") or "", _role(request), _q(request)
    )
    return json_response(result, status=_kind_status(result))


async def ops_field_season_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    body.setdefault("field_id", request.match_info.get("item_id"))
    result = await get_agro_ops_service().create_season(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_field_work_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    body.setdefault("field_id", request.match_info.get("item_id"))
    result = await get_agro_ops_service().create_work(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_field_harvest_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    body.setdefault("field_id", request.match_info.get("item_id"))
    result = await get_agro_ops_service().record_harvest(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_field_issue_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    body.setdefault("field_id", request.match_info.get("item_id"))
    result = await get_agro_ops_service().create_field_issue(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_work_status_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().set_work_status(
        _org(request, body), request.match_info.get("item_id") or "", body, _role(request, body)
    )
    return json_response(result, status=_kind_status(result))


async def ops_machine_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().create_machine(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_implement_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().create_implement(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_material_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().create_material(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_material_move_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().material_move(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_material_issue_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().issue_to_field(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_maintenance_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().create_maintenance(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_harvest_plan_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().create_harvest_plan(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_harvest_actual_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().record_harvest(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_harvest_warehouse_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().harvest_to_warehouse(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_field_cost_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().add_field_cost(_org(request, body), body, _role(request, body))
    return json_response(result, status=_kind_status(result, created=True))


async def ops_production_bootstrap_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().bootstrap_production_demo(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result, created=not result.get("already")))


async def ops_production_alerts_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().evaluate_production_alerts(_org(request, body), _role(request, body))
    return json_response(result, status=_kind_status(result))


# --- AGRO 2.6 operational handlers ---

async def ops_field_update_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().update_field(
        _org(request, body), request.match_info.get("item_id") or "", body, _role(request, body)
    )
    return json_response(result, status=_kind_status(result))


async def ops_field_archive_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().archive_field(
        _org(request, body), request.match_info.get("item_id") or "", _role(request, body)
    )
    return json_response(result, status=_kind_status(result))


async def ops_agro_crops_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        return json_response(await svc.list_agro_crops(org, role, _q(request)), status=_kind_status({"ok": True}))
    result = await svc.create_agro_crop(org, body, role)
    return json_response(result, status=_kind_status(result, created=True))


async def ops_agro_crop_item_handler(request: web.Request) -> web.Response:
    body = await _read_json(request) if request.method != "GET" else {}
    svc = get_agro_ops_service()
    item_id = request.match_info.get("item_id") or ""
    org, role = _org(request, body), _role(request, body)
    if request.method == "POST" and (body.get("archive") or request.rel_url.query.get("archive")):
        result = await svc.archive_agro_crop(org, item_id, role)
        return json_response(result, status=_kind_status(result))
    result = await svc.update_agro_crop(org, item_id, body, role)
    return json_response(result, status=_kind_status(result))


async def ops_sowings_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_sowings(org, role, _q(request))
        return json_response(result, status=_kind_status(result))
    result = await svc.create_sowing(org, body, role)
    return json_response(result, status=_kind_status(result, created=True))


async def ops_sowing_status_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().set_sowing_status(
        _org(request, body), request.match_info.get("item_id") or "", body, _role(request, body)
    )
    return json_response(result, status=_kind_status(result))


async def ops_works_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_works(org, role, _q(request))
        return json_response(result, status=_kind_status(result))
    result = await svc.create_work_order(org, body, role)
    return json_response(result, status=_kind_status(result, created=True))


async def ops_machines_list_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_machines(org, role, _q(request))
        return json_response(result, status=_kind_status(result))
    result = await svc.create_machine(org, body, role)
    return json_response(result, status=_kind_status(result, created=True))


async def ops_machine_360_handler(request: web.Request) -> web.Response:
    result = await get_agro_ops_service().machine_360(
        _org(request), request.match_info.get("item_id") or "", _role(request)
    )
    return json_response(result, status=_kind_status(result))


async def ops_machine_update_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_agro_ops_service().update_machine(
        _org(request, body), request.match_info.get("item_id") or "", body, _role(request, body)
    )
    return json_response(result, status=_kind_status(result))


async def ops_harvests_list_handler(request: web.Request) -> web.Response:
    svc = get_agro_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_harvests(org, role, _q(request))
        return json_response(result, status=_kind_status(result))
    result = await svc.record_harvest(org, body, role)
    return json_response(result, status=_kind_status(result, created=True))


async def ops_kpis_26_handler(request: web.Request) -> web.Response:
    result = await get_agro_ops_service().production_kpis_26(_org(request), _role(request))
    return json_response(result, status=_kind_status(result))

