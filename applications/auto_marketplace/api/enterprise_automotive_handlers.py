"""API handlers — Enterprise Automotive Suite (Sprint 13.0)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return auto_marketplace.enterprise_automotive


async def ea_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "auto_marketplace_ready": health.get("auto_marketplace_ready"),
            "auto_ai_ready": health.get("auto_ai_ready"),
            "dealer_platform_ready": health.get("dealer_platform_ready"),
            "enterprise_automotive_suite_ready": health.get("enterprise_automotive_suite_ready"),
            "suite": _suite().status(),
        }
    )


async def ea_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ea_marketplace_handler(request: web.Request) -> web.Response:
    try:
        core = _suite().marketplace
        if request.method == "GET":
            return json_response({"vehicles": core.list_vehicles(request.rel_url.query.get("type")), "status": core.status()})
        body = await _read_json(request)
        action = body.get("action", "vehicle")
        if action == "dealer":
            return json_response(core.register_dealer(name=body.get("name", ""), region=body.get("region", ""), contact=body.get("contact", "")), status=201)
        if action == "customer":
            return json_response(core.register_customer(name=body.get("name", ""), email=body.get("email", ""), phone=body.get("phone", "")), status=201)
        if action == "vin":
            return json_response(core.register_vin(vin=body.get("vin", ""), make=body.get("make", ""), model=body.get("model", ""), year=body.get("year")), status=201)
        if action == "auction":
            return json_response(core.create_auction(vehicle_id=body.get("vehicle_id", ""), reserve_price=float(body.get("reserve_price", 0) or 0)), status=201)
        if action == "import":
            return json_response(core.register_import(origin=body.get("origin", ""), vehicle_count=int(body.get("vehicle_count", 1) or 1), notes=body.get("notes", "")), status=201)
        if action == "inventory":
            return json_response(core.inventory_update(body.get("vehicle_id", ""), status=body.get("status", "in_stock")))
        return json_response(
            core.register_vehicle(
                vin=body.get("vin", ""),
                vehicle_type=body.get("vehicle_type", "car"),
                make=body.get("make", ""),
                model=body.get("model", ""),
                year=body.get("year"),
                price=float(body.get("price", 0) or 0),
                dealer_id=body.get("dealer_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ea_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        capability = body.get("capability") or body.get("action", "vin_decoder")
        return json_response(ai.run(capability=capability, **{k: v for k, v in body.items() if k not in ("capability", "action")}), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ea_sales_handler(request: web.Request) -> web.Response:
    try:
        sales = _suite().sales
        if request.method == "GET":
            return json_response({"sales": sales.list_sales(request.rel_url.query.get("action")), "status": sales.status()})
        body = await _read_json(request)
        if body.get("action") == "bid" or body.get("sale_action") == "bid":
            return json_response(
                sales.place_bid(auction_id=body.get("auction_id", ""), bidder_id=body.get("bidder_id", ""), amount=float(body.get("amount", 0) or 0)),
                status=201,
            )
        return json_response(
            sales.create(
                action=body.get("action", "buy"),
                vehicle_id=body.get("vehicle_id", ""),
                customer_id=body.get("customer_id", ""),
                dealer_id=body.get("dealer_id", ""),
                amount=float(body.get("amount", 0) or 0),
                metadata=body.get("metadata"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ea_crm_handler(request: web.Request) -> web.Response:
    try:
        crm = _suite().crm
        if request.method == "GET":
            return json_response({"funnel": crm.funnel_snapshot(), "status": crm.status()})
        body = await _read_json(request)
        action = body.get("action", "lead")
        if action == "funnel":
            return json_response(crm.advance_funnel(body.get("lead_id", ""), stage=body.get("stage", "contacted")))
        if action == "communicate":
            return json_response(
                crm.communicate(channel=body.get("channel", "email"), recipient=body.get("recipient", ""), message=body.get("message", ""), related_id=body.get("related_id", "")),
                status=201,
            )
        if action == "notify":
            return json_response(crm.notify(recipient=body.get("recipient", ""), title=body.get("title", ""), body=body.get("body", "")), status=201)
        if action == "followup":
            return json_response(
                crm.schedule_followup(lead_id=body.get("lead_id", ""), due_at=body.get("due_at", ""), note=body.get("note", "")),
                status=201,
            )
        return json_response(
            crm.create_lead(name=body.get("name", ""), interest=body.get("interest", ""), source=body.get("source", "web"), dealer_id=body.get("dealer_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ea_analytics_handler(request: web.Request) -> web.Response:
    try:
        analytics = _suite().analytics
        if request.method == "GET":
            return json_response({"reports": analytics.list_reports(request.rel_url.query.get("type")), "status": analytics.status()})
        body = await _read_json(request)
        return json_response(analytics.generate(report_type=body.get("report_type", "market"), title=body.get("title", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ea_integrations_handler(request: web.Request) -> web.Response:
    try:
        integ = _suite().integrations
        if request.method == "GET":
            return json_response({"connections": integ.list_connections(), "status": integ.status()})
        body = await _read_json(request)
        action = body.get("action", "connect")
        if action == "dispatch":
            return json_response(integ.dispatch(channel=body.get("channel", "email"), payload=body.get("payload")), status=201)
        return json_response(
            integ.connect(channel=body.get("channel", "email"), endpoint=body.get("endpoint", ""), credentials=body.get("credentials")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ea_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "dealer"), dealer_id=request.rel_url.query.get("dealer_id", "")))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "dealer"), dealer_id=body.get("dealer_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
