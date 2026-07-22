"""API handlers — Dealer CRM (Sprint 13.3)."""

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
    return auto_marketplace.dealer_crm


async def dc_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "dealer_crm_ready": health.get("dealer_crm_ready"),
            "trade_in_ai_ready": health.get("trade_in_ai_ready"),
            "inventory_intelligence_ready": health.get("inventory_intelligence_ready"),
            "sales_ai_ready": health.get("sales_ai_ready"),
            "suite": _suite().status(),
        }
    )


async def dc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def dc_crm_handler(request: web.Request) -> web.Response:
    try:
        crm = _suite().crm
        if request.method == "GET":
            return json_response({"pipeline": crm.pipeline_snapshot(), "status": crm.status()})
        body = await _read_json(request)
        action = body.get("action", "lead")
        if action == "dealership":
            return json_response(crm.create_dealership(name=body.get("name", ""), region=body.get("region", ""), contact=body.get("contact", "")), status=201)
        if action == "customer":
            return json_response(crm.create_customer(name=body.get("name", ""), email=body.get("email", ""), phone=body.get("phone", ""), dealership_id=body.get("dealership_id", "")), status=201)
        if action == "pipeline":
            return json_response(crm.advance_pipeline(body.get("lead_id", ""), stage=body.get("stage", "contacted")))
        if action == "contact":
            return json_response(crm.log_contact(channel=body.get("channel", "email"), related_id=body.get("related_id", ""), summary=body.get("summary", ""), direction=body.get("direction", "outbound")), status=201)
        if action == "task":
            return json_response(crm.create_task(title=body.get("title", ""), assignee=body.get("assignee", ""), due_at=body.get("due_at", ""), related_id=body.get("related_id", "")), status=201)
        if action == "appointment":
            return json_response(
                crm.schedule_appointment(
                    title=body.get("title", ""),
                    starts_at=body.get("starts_at", ""),
                    ends_at=body.get("ends_at", ""),
                    customer_id=body.get("customer_id", ""),
                    dealership_id=body.get("dealership_id", ""),
                ),
                status=201,
            )
        return json_response(
            crm.create_lead(
                name=body.get("name", ""),
                interest=body.get("interest", ""),
                source=body.get("source", "web"),
                dealership_id=body.get("dealership_id", ""),
                customer_id=body.get("customer_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dc_tradein_handler(request: web.Request) -> web.Response:
    try:
        tradein = _suite().tradein
        if request.method == "GET":
            return json_response(tradein.status())
        body = await _read_json(request)
        action = body.get("action", "evaluate")
        if action == "offer":
            return json_response(tradein.generate_offer(body.get("evaluation_id", ""), customer_id=body.get("customer_id", "")), status=201)
        return json_response(
            tradein.evaluate(
                vin=body.get("vin", ""),
                mileage=int(body.get("mileage", 50000) or 50000),
                damage_score=float(body.get("damage_score", 0.2) or 0.2),
                market_value=float(body.get("market_value", 18000) or 18000),
                inspection_ref=body.get("inspection_ref", ""),
                vin_decode_ref=body.get("vin_decode_ref", ""),
                target_margin=float(body.get("target_margin", 0.12) or 0.12),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dc_inventory_handler(request: web.Request) -> web.Response:
    try:
        inventory = _suite().inventory
        if request.method == "GET":
            vin = request.rel_url.query.get("vin")
            status = request.rel_url.query.get("status")
            if vin:
                return json_response({"items": inventory.search_vin(vin)})
            return json_response({"items": inventory.list_by_status(status), "status": inventory.status()})
        body = await _read_json(request)
        action = body.get("action", "add")
        if action == "status":
            return json_response(inventory.update_status(body.get("inventory_id", ""), status=body.get("status", "available")))
        if action == "optimize":
            return json_response(inventory.optimize(dealership_id=body.get("dealership_id", "")), status=201)
        if action == "recommend":
            return json_response(inventory.recommend(budget=float(body.get("budget", 0) or 0), make=body.get("make", "")), status=201)
        return json_response(
            inventory.add_vehicle(
                vin=body.get("vin", ""),
                make=body.get("make", ""),
                model=body.get("model", ""),
                year=body.get("year"),
                price=float(body.get("price", 0) or 0),
                warehouse=body.get("warehouse", "main"),
                dealership_id=body.get("dealership_id", ""),
                status=body.get("status", "available"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dc_sales_handler(request: web.Request) -> web.Response:
    try:
        sales = _suite().sales_ai
        if request.method == "GET":
            return json_response(sales.status())
        body = await _read_json(request)
        action = body.get("action", "qualify")
        if action == "intent":
            return json_response(sales.predict_intent(customer_id=body.get("customer_id", ""), signals=body.get("signals")), status=201)
        if action == "negotiate":
            return json_response(
                sales.negotiate(list_price=float(body.get("list_price", 0) or 0), customer_offer=float(body.get("customer_offer", 0) or 0)),
                status=201,
            )
        if action == "forecast":
            return json_response(
                sales.forecast(dealership_id=body.get("dealership_id", ""), horizon_days=int(body.get("horizon_days", 30) or 30)),
                status=201,
            )
        return json_response(
            sales.qualify_lead(lead_id=body.get("lead_id", ""), budget=float(body.get("budget", 0) or 0), intent=body.get("intent", "browse")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dc_analytics_handler(request: web.Request) -> web.Response:
    try:
        analytics = _suite().analytics
        if request.method == "GET":
            return json_response(
                analytics.render(
                    dashboard_type=request.rel_url.query.get("type", "sales"),
                    dealership_id=request.rel_url.query.get("dealership_id", ""),
                )
            )
        body = await _read_json(request)
        return json_response(
            analytics.render(dashboard_type=body.get("dashboard_type", "sales"), dealership_id=body.get("dealership_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dc_integrations_handler(request: web.Request) -> web.Response:
    try:
        integ = _suite().integrations
        if request.method == "GET":
            return json_response({"connections": integ.list_connections(), "status": integ.status()})
        body = await _read_json(request)
        return json_response(integ.connect(target=body.get("target", "marketplace"), endpoint=body.get("endpoint", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)
