"""API handlers — Agro Supply Chain (Sprint 14.5)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.middleware import json_response
from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return agro_enterprise.supply_chain


async def sc_health_handler(request: web.Request) -> web.Response:
    health = agro_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "supply_chain_ready": health.get("supply_chain_ready"),
            "grain_elevator_ready": health.get("grain_elevator_ready"),
            "warehouse_platform_ready": health.get("warehouse_platform_ready"),
            "export_logistics_ready": health.get("export_logistics_ready"),
            "trading_platform_ready": health.get("trading_platform_ready"),
            "suite": _suite().status(),
        }
    )


async def sc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def sc_supply_handler(request: web.Request) -> web.Response:
    try:
        supply = _suite().supply
        if request.method == "GET":
            return json_response(supply.status())
        body = await _read_json(request)
        action = body.get("action", "node")
        if action == "dc":
            return json_response(
                supply.add_distribution_center(
                    name=body.get("name", ""), capacity_t=float(body.get("capacity_t", 10000) or 10000)
                ),
                status=201,
            )
        if action == "shipment":
            return json_response(
                supply.track_shipment(
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    commodity=body.get("commodity", ""),
                    tons=float(body.get("tons", 0) or 0),
                ),
                status=201,
            )
        if action == "supply_plan":
            return json_response(
                supply.supply_plan(
                    commodity=body.get("commodity", ""),
                    tons=float(body.get("tons", 0) or 0),
                    horizon_days=int(body.get("horizon_days", 30) or 30),
                ),
                status=201,
            )
        if action == "demand_plan":
            return json_response(
                supply.demand_plan(
                    commodity=body.get("commodity", ""),
                    tons=float(body.get("tons", 0) or 0),
                    market=body.get("market", "EU"),
                ),
                status=201,
            )
        if action == "order":
            return json_response(
                supply.create_order(
                    buyer=body.get("buyer", ""),
                    commodity=body.get("commodity", ""),
                    tons=float(body.get("tons", 0) or 0),
                    price=float(body.get("price", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            supply.add_node(
                name=body.get("name", ""),
                node_type=body.get("node_type", "hub"),
                region=body.get("region", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sc_elevator_handler(request: web.Request) -> web.Response:
    try:
        elev = _suite().elevator
        if request.method == "GET":
            eid = request.rel_url.query.get("elevator_id")
            if eid:
                return json_response(elev.capacity(eid))
            return json_response(elev.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "silo":
            return json_response(
                elev.register_silo(
                    elevator_id=body.get("elevator_id", ""),
                    capacity_t=float(body.get("capacity_t", 1000) or 1000),
                    commodity=body.get("commodity", "wheat"),
                ),
                status=201,
            )
        if action == "intake":
            return json_response(
                elev.intake(body.get("silo_id", ""), tons=float(body.get("tons", 0) or 0)),
                status=201,
            )
        if action == "dispatch":
            return json_response(
                elev.dispatch(body.get("silo_id", ""), tons=float(body.get("tons", 0) or 0)),
                status=201,
            )
        if action == "dry":
            return json_response(
                elev.dry(
                    body.get("silo_id", ""),
                    target_moisture_pct=float(body.get("target_moisture_pct", 14) or 14),
                ),
                status=201,
            )
        if action == "clean":
            return json_response(elev.clean(body.get("silo_id", "")), status=201)
        if action == "monitor":
            return json_response(
                elev.monitor(
                    body.get("silo_id", ""),
                    temp_c=float(body.get("temp_c", 18) or 18),
                    humidity_pct=float(body.get("humidity_pct", 55) or 55),
                    aeration=bool(body.get("aeration", False)),
                ),
                status=201,
            )
        return json_response(
            elev.register_elevator(name=body.get("name", ""), location=body.get("location", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sc_quality_handler(request: web.Request) -> web.Response:
    try:
        quality = _suite().quality
        if request.method == "GET":
            return json_response(quality.status())
        body = await _read_json(request)
        action = body.get("action", "inspect")
        if action == "certificate":
            return json_response(quality.certificate(body.get("inspection_id", "")), status=201)
        return json_response(
            quality.inspect(
                lot_id=body.get("lot_id", ""),
                moisture_pct=float(body.get("moisture_pct", 14) or 14),
                protein_pct=float(body.get("protein_pct", 12) or 12),
                oil_pct=float(body.get("oil_pct", 0) or 0),
                foreign_material_pct=float(body.get("foreign_material_pct", 1) or 1),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sc_warehouse_handler(request: web.Request) -> web.Response:
    try:
        wh = _suite().warehouse
        if request.method == "GET":
            return json_response(wh.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "inventory":
            return json_response(
                wh.add_inventory(
                    warehouse_id=body.get("warehouse_id", ""),
                    sku=body.get("sku", ""),
                    tons=float(body.get("tons", 0) or 0),
                    lot=body.get("lot", ""),
                    batch=body.get("batch", ""),
                ),
                status=201,
            )
        if action == "optimize":
            return json_response(wh.optimize(body.get("warehouse_id", "")), status=201)
        return json_response(
            wh.register_warehouse(
                name=body.get("name", ""), cold_storage=bool(body.get("cold_storage", False))
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sc_logistics_handler(request: web.Request) -> web.Response:
    try:
        logistics = _suite().logistics
        if request.method == "GET":
            return json_response(logistics.status())
        body = await _read_json(request)
        action = body.get("action", "truck")
        if action == "rail":
            return json_response(
                logistics.register_rail(
                    wagon=body.get("wagon", ""), capacity_t=float(body.get("capacity_t", 60) or 60)
                ),
                status=201,
            )
        if action == "container":
            return json_response(
                logistics.register_container(code=body.get("code", ""), teu=float(body.get("teu", 1) or 1)),
                status=201,
            )
        if action == "route":
            return json_response(
                logistics.optimize_route(
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    mode=body.get("mode", "truck"),
                ),
                status=201,
            )
        if action == "freight":
            return json_response(
                logistics.freight_plan(
                    commodity=body.get("commodity", ""),
                    tons=float(body.get("tons", 0) or 0),
                    mode=body.get("mode", "truck"),
                ),
                status=201,
            )
        if action == "track":
            return json_response(
                logistics.track_cargo(
                    shipment_ref=body.get("shipment_ref", ""),
                    lat=float(body.get("lat", 0) or 0),
                    lon=float(body.get("lon", 0) or 0),
                ),
                status=201,
            )
        if action == "delivery":
            return json_response(
                logistics.schedule_delivery(
                    shipment_ref=body.get("shipment_ref", ""),
                    window_start=body.get("window_start", ""),
                    window_end=body.get("window_end", ""),
                ),
                status=201,
            )
        return json_response(
            logistics.register_truck(
                plate=body.get("plate", ""), capacity_t=float(body.get("capacity_t", 25) or 25)
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sc_export_handler(request: web.Request) -> web.Response:
    try:
        export = _suite().export
        if request.method == "GET":
            return json_response(export.status())
        body = await _read_json(request)
        action = body.get("action", "contract")
        if action == "buyer":
            return json_response(
                export.register_buyer(name=body.get("name", ""), country=body.get("country", "")),
                status=201,
            )
        if action == "price":
            return json_response(
                export.price_quote(commodity=body.get("commodity", ""), market=body.get("market", "CBOT")),
                status=201,
            )
        if action == "docs":
            return json_response(export.export_docs(contract_id=body.get("contract_id", "")), status=201)
        if action == "desk":
            return json_response(
                export.trading_desk_order(
                    side=body.get("side", "sell"),
                    commodity=body.get("commodity", ""),
                    tons=float(body.get("tons", 0) or 0),
                    price=float(body.get("price", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            export.create_contract(
                buyer=body.get("buyer", ""),
                commodity=body.get("commodity", ""),
                tons=float(body.get("tons", 0) or 0),
                price=float(body.get("price", 0) or 0),
                incoterm=body.get("incoterm", "FOB"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sc_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "supply_chain")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "supply_chain")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sc_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "supply_chain"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
