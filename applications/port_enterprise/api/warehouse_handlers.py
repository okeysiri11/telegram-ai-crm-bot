"""API handlers — Warehouse & Distribution (Sprint 15.5)."""

from __future__ import annotations

from aiohttp import web

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.middleware import json_response
from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return port_enterprise.warehouse_distribution


async def wd_health_handler(request: web.Request) -> web.Response:
    health = port_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "warehouse_platform_ready": health.get("warehouse_platform_ready"),
            "distribution_centers_ready": health.get("distribution_centers_ready"),
            "free_economic_zones_ready": health.get("free_economic_zones_ready"),
            "warehouse_automation_ready": health.get("warehouse_automation_ready"),
            "ai_warehouse_ready": health.get("ai_warehouse_ready"),
            "suite": _suite().status(),
        }
    )


async def wd_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def wd_warehouse_handler(request: web.Request) -> web.Response:
    try:
        wh = _suite().warehouse
        if request.method == "GET":
            return json_response(wh.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "zone":
            return json_response(
                wh.create_zone(
                    warehouse_id=body.get("warehouse_id", ""),
                    name=body.get("name", ""),
                    zone_type=body.get("zone_type", "general"),
                ),
                status=201,
            )
        if action == "receive":
            return json_response(
                wh.receive(
                    warehouse_id=body.get("warehouse_id", ""),
                    sku=body.get("sku", ""),
                    qty=float(body.get("qty", 0) or 0),
                    zone_id=body.get("zone_id", ""),
                ),
                status=201,
            )
        if action == "ship":
            return json_response(
                wh.ship(
                    warehouse_id=body.get("warehouse_id", ""),
                    sku=body.get("sku", ""),
                    qty=float(body.get("qty", 0) or 0),
                ),
                status=201,
            )
        if action == "crossdock":
            return json_response(
                wh.cross_dock(
                    warehouse_id=body.get("warehouse_id", ""),
                    inbound_ref=body.get("inbound_ref", ""),
                    outbound_ref=body.get("outbound_ref", ""),
                ),
                status=201,
            )
        if action == "cold":
            return json_response(
                wh.cold_storage(
                    warehouse_id=body.get("warehouse_id", ""),
                    sku=body.get("sku", ""),
                    temp_c=float(body.get("temp_c", -18) or -18),
                ),
                status=201,
            )
        if action == "hazardous":
            return json_response(
                wh.hazardous_storage(
                    warehouse_id=body.get("warehouse_id", ""),
                    sku=body.get("sku", ""),
                    hazard_class=body.get("hazard_class", ""),
                ),
                status=201,
            )
        if action == "optimize":
            return json_response(wh.optimize_inventory(warehouse_id=body.get("warehouse_id", "")), status=201)
        return json_response(
            wh.register_warehouse(
                name=body.get("name", ""),
                capacity_teu=float(body.get("capacity_teu", 5000) or 5000),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wd_distribution_handler(request: web.Request) -> web.Response:
    try:
        dist = _suite().distribution
        if request.method == "GET":
            return json_response(dist.status())
        body = await _read_json(request)
        action = body.get("action", "dc")
        if action == "hub":
            return json_response(
                dist.register_hub(name=body.get("name", ""), region=body.get("region", "")),
                status=201,
            )
        if action == "consolidate":
            refs = body.get("order_refs") if isinstance(body.get("order_refs"), list) else []
            return json_response(
                dist.consolidate(dc_id=body.get("dc_id", ""), order_refs=refs),
                status=201,
            )
        if action == "fulfill":
            return json_response(
                dist.fulfill(dc_id=body.get("dc_id", ""), order_ref=body.get("order_ref", "")),
                status=201,
            )
        if action == "allocate":
            return json_response(
                dist.allocate(
                    dc_id=body.get("dc_id", ""),
                    sku=body.get("sku", ""),
                    qty=float(body.get("qty", 0) or 0),
                ),
                status=201,
            )
        if action == "load":
            return json_response(
                dist.load_plan(
                    dc_id=body.get("dc_id", ""),
                    vehicle_ref=body.get("vehicle_ref", ""),
                    teu=float(body.get("teu", 0) or 0),
                ),
                status=201,
            )
        if action == "dispatch":
            return json_response(
                dist.dispatch(
                    dc_id=body.get("dc_id", ""),
                    destination=body.get("destination", ""),
                    vehicle_ref=body.get("vehicle_ref", ""),
                ),
                status=201,
            )
        return json_response(
            dist.register_dc(
                name=body.get("name", ""),
                region=body.get("region", ""),
                capacity_teu=float(body.get("capacity_teu", 10000) or 10000),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wd_fez_handler(request: web.Request) -> web.Response:
    try:
        fez = _suite().fez
        if request.method == "GET":
            return json_response(fez.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "resident":
            return json_response(
                fez.register_resident(fez_id=body.get("fez_id", ""), company_name=body.get("company_name", "")),
                status=201,
            )
        if action == "tax":
            return json_response(
                fez.tax_benefit(
                    fez_id=body.get("fez_id", ""),
                    benefit_type=body.get("benefit_type", "corporate_tax"),
                    rate_pct=float(body.get("rate_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "duty_free":
            return json_response(
                fez.duty_free(
                    fez_id=body.get("fez_id", ""),
                    operation_ref=body.get("operation_ref", ""),
                    value=float(body.get("value", 0) or 0),
                ),
                status=201,
            )
        if action == "bonded":
            return json_response(
                fez.bonded_warehouse(
                    fez_id=body.get("fez_id", ""),
                    name=body.get("name", ""),
                    capacity_teu=float(body.get("capacity_teu", 2000) or 2000),
                ),
                status=201,
            )
        if action == "customs":
            return json_response(
                fez.customs_link(
                    fez_id=body.get("fez_id", ""),
                    customs_office_ref=body.get("customs_office_ref", ""),
                ),
                status=201,
            )
        if action == "compliance":
            return json_response(
                fez.compliance_monitor(fez_id=body.get("fez_id", ""), status=body.get("status", "compliant")),
                status=201,
            )
        return json_response(
            fez.register_fez(name=body.get("name", ""), region=body.get("region", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wd_inventory_handler(request: web.Request) -> web.Response:
    try:
        inv = _suite().inventory
        if request.method == "GET":
            return json_response(inv.status())
        body = await _read_json(request)
        action = body.get("action", "item")
        if action == "batch":
            return json_response(
                inv.track_batch(
                    sku=body.get("sku", ""),
                    batch_no=body.get("batch_no", ""),
                    qty=float(body.get("qty", 0) or 0),
                ),
                status=201,
            )
        if action == "lot":
            return json_response(
                inv.track_lot(
                    sku=body.get("sku", ""),
                    lot_no=body.get("lot_no", ""),
                    qty=float(body.get("qty", 0) or 0),
                ),
                status=201,
            )
        if action == "serial":
            return json_response(
                inv.track_serial(sku=body.get("sku", ""), serial_no=body.get("serial_no", "")),
                status=201,
            )
        if action == "barcode":
            return json_response(
                inv.barcode(sku=body.get("sku", ""), code=body.get("code", "")),
                status=201,
            )
        if action == "qr":
            return json_response(
                inv.qr_code(sku=body.get("sku", ""), payload=body.get("payload", "")),
                status=201,
            )
        if action == "rfid":
            return json_response(
                inv.rfid(sku=body.get("sku", ""), tag_id=body.get("tag_id", "")),
                status=201,
            )
        if action == "forecast":
            return json_response(
                inv.forecast(
                    sku=body.get("sku", ""),
                    days=int(body.get("days", 30) or 30),
                    baseline_qty=float(body.get("baseline_qty", 100) or 100),
                ),
                status=201,
            )
        return json_response(
            inv.upsert_item(
                warehouse_id=body.get("warehouse_id", ""),
                sku=body.get("sku", ""),
                qty=float(body.get("qty", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wd_automation_handler(request: web.Request) -> web.Response:
    try:
        auto = _suite().automation
        if request.method == "GET":
            return json_response(auto.status())
        body = await _read_json(request)
        action = body.get("action", "storage")
        if action == "picking":
            return json_response(
                auto.optimize_picking(
                    warehouse_id=body.get("warehouse_id", ""),
                    order_ref=body.get("order_ref", ""),
                ),
                status=201,
            )
        if action == "packing":
            return json_response(
                auto.optimize_packing(
                    warehouse_id=body.get("warehouse_id", ""),
                    order_ref=body.get("order_ref", ""),
                ),
                status=201,
            )
        if action == "sort":
            return json_response(
                auto.sort(
                    warehouse_id=body.get("warehouse_id", ""),
                    lane=body.get("lane", ""),
                    items=int(body.get("items", 0) or 0),
                ),
                status=201,
            )
        if action == "loading":
            return json_response(
                auto.optimize_loading(
                    warehouse_id=body.get("warehouse_id", ""),
                    dock_id=body.get("dock_id", ""),
                ),
                status=201,
            )
        if action == "dock":
            return json_response(
                auto.schedule_dock(
                    warehouse_id=body.get("warehouse_id", ""),
                    dock_name=body.get("dock_name", ""),
                    window_start=body.get("window_start", ""),
                ),
                status=201,
            )
        if action == "agv":
            return json_response(
                auto.assign_agv(warehouse_id=body.get("warehouse_id", ""), task=body.get("task", "")),
                status=201,
            )
        if action == "robot":
            return json_response(
                auto.assign_robot(
                    warehouse_id=body.get("warehouse_id", ""),
                    robot_type=body.get("robot_type", "picker"),
                    task=body.get("task", ""),
                ),
                status=201,
            )
        return json_response(
            auto.storage_plan(
                warehouse_id=body.get("warehouse_id", ""),
                sku=body.get("sku", ""),
                slots=int(body.get("slots", 1) or 1),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wd_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "demand")
        if action == "space":
            return json_response(ai.space_optimize(warehouse_id=body.get("warehouse_id", "")), status=201)
        if action == "inventory":
            return json_response(ai.inventory_optimize(warehouse_id=body.get("warehouse_id", "")), status=201)
        if action == "labor":
            return json_response(
                ai.labor_optimize(
                    warehouse_id=body.get("warehouse_id", ""),
                    headcount=int(body.get("headcount", 10) or 10),
                ),
                status=201,
            )
        if action == "energy":
            return json_response(ai.energy_optimize(warehouse_id=body.get("warehouse_id", "")), status=201)
        if action == "flow":
            return json_response(ai.cargo_flow_predict(warehouse_id=body.get("warehouse_id", "")), status=201)
        if action == "ops":
            return json_response(
                ai.operational_analytics(warehouse_id=body.get("warehouse_id", "")),
                status=201,
            )
        return json_response(
            ai.demand_forecast(
                sku=body.get("sku", ""),
                days=int(body.get("days", 30) or 30),
                baseline=float(body.get("baseline", 100) or 100),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wd_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "warehouse")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "warehouse")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wd_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "warehouse"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
