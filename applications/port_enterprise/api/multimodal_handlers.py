"""API handlers — Multimodal Logistics (Sprint 15.3)."""

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
    return port_enterprise.multimodal_logistics


async def ml_health_handler(request: web.Request) -> web.Response:
    health = port_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "rail_logistics_ready": health.get("rail_logistics_ready"),
            "truck_logistics_ready": health.get("truck_logistics_ready"),
            "multimodal_platform_ready": health.get("multimodal_platform_ready"),
            "shipment_management_ready": health.get("shipment_management_ready"),
            "ai_logistics_ready": health.get("ai_logistics_ready"),
            "suite": _suite().status(),
        }
    )


async def ml_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ml_rail_handler(request: web.Request) -> web.Response:
    try:
        rail = _suite().rail
        if request.method == "GET":
            return json_response(rail.status())
        body = await _read_json(request)
        action = body.get("action", "network")
        if action == "terminal":
            return json_response(
                rail.register_terminal(name=body.get("name", ""), network_id=body.get("network_id", "")),
                status=201,
            )
        if action == "train":
            return json_response(
                rail.register_train(name=body.get("name", ""), terminal_id=body.get("terminal_id", "")),
                status=201,
            )
        if action == "wagon":
            return json_response(
                rail.register_wagon(
                    code=body.get("code", ""),
                    train_id=body.get("train_id", ""),
                    capacity_teu=float(body.get("capacity_teu", 2) or 2),
                ),
                status=201,
            )
        if action == "locomotive":
            return json_response(
                rail.register_locomotive(
                    name=body.get("name", ""),
                    power_kw=float(body.get("power_kw", 4000) or 4000),
                ),
                status=201,
            )
        if action == "schedule":
            return json_response(
                rail.schedule(
                    train_id=body.get("train_id", ""),
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    departs_at=body.get("departs_at", ""),
                ),
                status=201,
            )
        if action == "track":
            return json_response(
                rail.track_cargo(
                    train_id=body.get("train_id", ""),
                    cargo_ref=body.get("cargo_ref", ""),
                    status=body.get("status", "in_transit"),
                ),
                status=201,
            )
        if action == "capacity":
            return json_response(
                rail.capacity_plan(
                    network_id=body.get("network_id", ""),
                    teu=float(body.get("teu", 0) or 0),
                    horizon_days=int(body.get("horizon_days", 30) or 30),
                ),
                status=201,
            )
        return json_response(
            rail.register_network(name=body.get("name", ""), region=body.get("region", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ml_truck_handler(request: web.Request) -> web.Response:
    try:
        truck = _suite().truck
        if request.method == "GET":
            return json_response(truck.status())
        body = await _read_json(request)
        action = body.get("action", "truck")
        if action == "trailer":
            return json_response(
                truck.register_trailer(code=body.get("code", ""), truck_id=body.get("truck_id", "")),
                status=201,
            )
        if action == "driver":
            return json_response(
                truck.register_driver(name=body.get("name", ""), license_no=body.get("license_no", "")),
                status=201,
            )
        if action == "dispatch":
            return json_response(
                truck.dispatch(
                    truck_id=body.get("truck_id", ""),
                    driver_id=body.get("driver_id", ""),
                    destination=body.get("destination", ""),
                ),
                status=201,
            )
        if action == "route":
            return json_response(
                truck.plan_route(
                    truck_id=body.get("truck_id", ""),
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                ),
                status=201,
            )
        if action == "track":
            return json_response(
                truck.track(
                    truck_id=body.get("truck_id", ""),
                    lat=float(body.get("lat", 0) or 0),
                    lon=float(body.get("lon", 0) or 0),
                ),
                status=201,
            )
        if action == "fuel":
            return json_response(
                truck.fuel(body.get("truck_id", ""), liters=float(body.get("liters", 0) or 0)),
                status=201,
            )
        if action == "maintain":
            return json_response(
                truck.maintain(
                    body.get("truck_id", ""),
                    work=body.get("work", "service"),
                    due_at=body.get("due_at", ""),
                ),
                status=201,
            )
        return json_response(
            truck.register_truck(
                plate=body.get("plate", ""),
                capacity_t=float(body.get("capacity_t", 20) or 20),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ml_multimodal_handler(request: web.Request) -> web.Response:
    try:
        mm = _suite().multimodal
        if request.method == "GET":
            return json_response(mm.status())
        body = await _read_json(request)
        action = body.get("action", "chain")
        if action == "transfer":
            return json_response(
                mm.mode_transfer(
                    chain_id=body.get("chain_id", ""),
                    from_mode=body.get("from_mode", "sea"),
                    to_mode=body.get("to_mode", "rail"),
                    location=body.get("location", ""),
                ),
                status=201,
            )
        if action == "container_transfer":
            return json_response(
                mm.container_transfer(
                    chain_id=body.get("chain_id", ""),
                    container_ref=body.get("container_ref", ""),
                    location=body.get("location", ""),
                ),
                status=201,
            )
        if action == "intermodal":
            modes = body.get("modes") if isinstance(body.get("modes"), list) else None
            return json_response(
                mm.intermodal_terminal(name=body.get("name", ""), modes=modes),
                status=201,
            )
        if action == "crossdock":
            return json_response(
                mm.cross_dock(
                    terminal_id=body.get("terminal_id", ""),
                    inbound=body.get("inbound", "rail"),
                    outbound=body.get("outbound", "truck"),
                ),
                status=201,
            )
        if action == "consolidate":
            refs = body.get("shipment_refs") if isinstance(body.get("shipment_refs"), list) else []
            return json_response(
                mm.consolidate(shipment_refs=refs, destination=body.get("destination", "")),
                status=201,
            )
        if action == "optimize":
            return json_response(mm.optimize_transport(chain_id=body.get("chain_id", "")), status=201)
        legs = body.get("legs") if isinstance(body.get("legs"), list) else None
        return json_response(mm.create_chain(name=body.get("name", ""), legs=legs), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ml_inland_handler(request: web.Request) -> web.Response:
    try:
        inland = _suite().inland
        if request.method == "GET":
            return json_response(inland.status())
        body = await _read_json(request)
        action = body.get("action", "dry_port")
        if action == "dc":
            return json_response(
                inland.register_dc(
                    name=body.get("name", ""),
                    capacity_teu=float(body.get("capacity_teu", 5000) or 5000),
                ),
                status=201,
            )
        if action == "hub":
            return json_response(inland.register_hub(name=body.get("name", "")), status=201)
        if action == "redistribute":
            return json_response(
                inland.redistribute(
                    from_site=body.get("from_site", ""),
                    to_site=body.get("to_site", ""),
                    teu=float(body.get("teu", 0) or 0),
                ),
                status=201,
            )
        if action == "storage":
            return json_response(
                inland.coordinate_storage(site=body.get("site", ""), teu=float(body.get("teu", 0) or 0)),
                status=201,
            )
        return json_response(
            inland.register_dry_port(name=body.get("name", ""), region=body.get("region", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ml_shipments_handler(request: web.Request) -> web.Response:
    try:
        shipments = _suite().shipments
        if request.method == "GET":
            return json_response(shipments.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        sid = body.get("shipment_id", "")
        if action == "track":
            return json_response(
                shipments.track(sid, status=body.get("status", "in_transit"), location=body.get("location", "")),
                status=201,
            )
        if action == "document":
            return json_response(
                shipments.document(sid, doc_type=body.get("doc_type", "cmr"), title=body.get("title", "")),
                status=201,
            )
        if action == "eta":
            return json_response(
                shipments.eta(sid, hours=float(body.get("hours", 24) or 24)),
                status=201,
            )
        if action == "delivery":
            return json_response(
                shipments.schedule_delivery(
                    sid,
                    window_start=body.get("window_start", ""),
                    window_end=body.get("window_end", ""),
                ),
                status=201,
            )
        if action == "pod":
            return json_response(
                shipments.proof_of_delivery(sid, signed_by=body.get("signed_by", "")),
                status=201,
            )
        return json_response(
            shipments.register(
                reference=body.get("reference", ""),
                origin=body.get("origin", ""),
                destination=body.get("destination", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ml_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "demand")
        if action == "route":
            return json_response(
                ai.optimize_route(
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    mode=body.get("mode", "truck"),
                ),
                status=201,
            )
        if action == "fleet":
            return json_response(
                ai.optimize_fleet(fleet_size=int(body.get("fleet_size", 10) or 10)),
                status=201,
            )
        if action == "traffic":
            return json_response(ai.traffic_prediction(corridor=body.get("corridor", "")), status=201)
        if action == "capacity":
            return json_response(
                ai.capacity_forecast(node=body.get("node", ""), teu=float(body.get("teu", 0) or 0)),
                status=201,
            )
        if action == "cost":
            return json_response(
                ai.cost_optimize(
                    shipment_id=body.get("shipment_id", ""),
                    baseline_cost=float(body.get("baseline_cost", 0) or 0),
                ),
                status=201,
            )
        if action == "delay":
            return json_response(
                ai.delay_predict(
                    shipment_id=body.get("shipment_id", ""),
                    risk=float(body.get("risk", 0.2) or 0.2),
                ),
                status=201,
            )
        if action == "carbon":
            return json_response(
                ai.carbon_analytics(
                    shipment_id=body.get("shipment_id", ""),
                    ton_km=float(body.get("ton_km", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            ai.demand_forecast(
                corridor=body.get("corridor", ""),
                teu=float(body.get("teu", 0) or 0),
                days=int(body.get("days", 30) or 30),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ml_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "multimodal")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "multimodal")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ml_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "logistics"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
