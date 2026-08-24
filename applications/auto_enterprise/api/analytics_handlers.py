"""HTTP handlers — Auto Ops director analytics / finance (AUTO 1.5)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_enterprise.api.middleware import json_response
from applications.auto_enterprise.api.ops_handlers import _actor, _org, _read_json, _role, _status
from services.auto_ops import get_auto_ops_service


def _q(request: web.Request, body: dict | None = None) -> dict[str, str]:
    out = {k: str(v) for k, v in request.rel_url.query.items()}
    for key, val in (body or {}).items():
        if val is None or isinstance(val, (dict, list)):
            continue
        out[str(key)] = str(val)
    return out


async def _call(request: web.Request, method: str, *, created: bool = False) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    fn = getattr(svc, method)
    result = await fn(_org(request, body), _role(request, body), _q(request, body), _actor(request))
    return json_response(result, status=_status(result, created=created))


async def analytics_director_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_director")


async def analytics_economics_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_economics")


async def analytics_ranking_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_ranking")


async def analytics_finance_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_finance")


async def analytics_cashflow_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_cashflow")


async def analytics_receivables_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_receivables")


async def analytics_sales_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_sales")


async def analytics_managers_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_managers")


async def analytics_logistics_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_logistics")


async def analytics_suppliers_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_suppliers")


async def analytics_customs_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_customs")


async def analytics_repair_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_repair")


async def analytics_documents_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_documents")


async def analytics_funnel_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_funnel")


async def analytics_risks_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_risks")


async def analytics_ai_handler(request: web.Request) -> web.Response:
    return await _call(request, "analytics_ai")


async def analytics_demo_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    result = await svc.seed_demo_analytics(_org(request, body), body, _role(request, body), _actor(request))
    return json_response(result, status=_status(result, created=True))


async def analytics_alerts_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    result = await svc.evaluate_analytics_alerts(_org(request, body), _role(request, body))
    return json_response(result, status=_status(result))


async def analytics_export_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    q = _q(request)
    result = await svc.analytics_export(_org(request), _role(request), q, _actor(request))
    raw = result.get("content")
    if result.get("ok") and isinstance(raw, (bytes, bytearray)):
        filename = str(result.get("filename") or "auto-export.csv")
        return web.Response(
            body=bytes(raw),
            headers={
                "Content-Type": "text/csv",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    return json_response(result, status=_status(result))


async def finance_accounts_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org, role = _org(request, body), _role(request, body)
    if request.method == "GET":
        result = await svc.list_finance_accounts(org, role)
        return json_response(result, status=_status(result))
    body.setdefault("source", "WEB")
    result = await svc.upsert_finance_account(org, body, role, _actor(request))
    return json_response(result, status=_status(result, created=True))
