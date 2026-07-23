"""API handlers — Port Enterprise (Sprint 15.0)."""

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


async def health_handler(request: web.Request) -> web.Response:
    return json_response(port_enterprise.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(port_enterprise.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ports_handler(request: web.Request) -> web.Response:
    try:
        ports = port_enterprise.ports
        if request.method == "GET":
            return json_response(ports.status())
        body = await _read_json(request)
        action = body.get("action", "port")
        if action == "terminal":
            return json_response(
                ports.register_terminal(
                    port_id=body.get("port_id", ""),
                    name=body.get("name", ""),
                    terminal_type=body.get("terminal_type", "container"),
                ),
                status=201,
            )
        if action == "dock":
            return json_response(
                ports.register_dock(terminal_id=body.get("terminal_id", ""), name=body.get("name", "")),
                status=201,
            )
        if action == "berth":
            return json_response(
                ports.register_berth(
                    dock_id=body.get("dock_id", ""),
                    name=body.get("name", ""),
                    length_m=float(body.get("length_m", 300) or 300),
                ),
                status=201,
            )
        if action == "warehouse":
            return json_response(
                ports.register_warehouse(
                    port_id=body.get("port_id", ""),
                    name=body.get("name", ""),
                    capacity_teu=float(body.get("capacity_teu", 1000) or 1000),
                ),
                status=201,
            )
        if action == "yard":
            return json_response(
                ports.register_yard(
                    port_id=body.get("port_id", ""),
                    name=body.get("name", ""),
                    capacity_teu=float(body.get("capacity_teu", 5000) or 5000),
                ),
                status=201,
            )
        if action == "equipment":
            return json_response(
                ports.register_equipment(
                    terminal_id=body.get("terminal_id", ""),
                    name=body.get("name", ""),
                    equipment_type=body.get("equipment_type", "crane"),
                ),
                status=201,
            )
        return json_response(
            ports.register_port(
                name=body.get("name", ""),
                unlocode=body.get("unlocode", ""),
                country=body.get("country", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def terminals_handler(request: web.Request) -> web.Response:
    try:
        terminals = port_enterprise.terminals
        if request.method == "GET":
            tid = request.rel_url.query.get("terminal_id")
            if tid:
                return json_response(terminals.utilization(tid))
            return json_response(terminals.status())
        body = await _read_json(request)
        return json_response(
            terminals.set_capacity(
                terminal_id=body.get("terminal_id", ""),
                capacity_teu=float(body.get("capacity_teu", 0) or 0),
                utilized_teu=float(body.get("utilized_teu", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cargo_handler(request: web.Request) -> web.Response:
    try:
        cargo = port_enterprise.cargo
        if request.method == "GET":
            return json_response(cargo.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "track":
            return json_response(
                cargo.track(
                    body.get("cargo_id", ""),
                    status=body.get("status", "in_transit"),
                    location=body.get("location", ""),
                ),
                status=201,
            )
        return json_response(
            cargo.register(
                description=body.get("description", ""),
                category=body.get("category", "general"),
                weight_t=float(body.get("weight_t", 0) or 0),
                port_id=body.get("port_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def shipping_handler(request: web.Request) -> web.Response:
    try:
        shipping = port_enterprise.shipping
        if request.method == "GET":
            return json_response(shipping.status())
        body = await _read_json(request)
        action = body.get("action", "line")
        if action == "carrier":
            return json_response(
                shipping.register_carrier(name=body.get("name", ""), mode=body.get("mode", "ocean")),
                status=201,
            )
        if action == "operator":
            return json_response(shipping.register_operator(name=body.get("name", "")), status=201)
        if action == "agency":
            return json_response(
                shipping.register_agency(name=body.get("name", ""), port_id=body.get("port_id", "")),
                status=201,
            )
        if action == "provider":
            return json_response(
                shipping.register_provider(name=body.get("name", ""), service=body.get("service", "pilotage")),
                status=201,
            )
        return json_response(
            shipping.register_line(name=body.get("name", ""), scac=body.get("scac", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def fleet_handler(request: web.Request) -> web.Response:
    try:
        fleet = port_enterprise.fleet
        if request.method == "GET":
            return json_response(fleet.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "status":
            return json_response(
                fleet.set_status(body.get("vessel_id", ""), status=body.get("status", "active")),
                status=201,
            )
        return json_response(
            fleet.register_vessel(
                name=body.get("name", ""),
                imo=body.get("imo", ""),
                flag=body.get("flag", ""),
                owner=body.get("owner", ""),
                loa_m=float(body.get("loa_m", 0) or 0),
                dwt=float(body.get("dwt", 0) or 0),
                operator_id=body.get("operator_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def operations_handler(request: web.Request) -> web.Response:
    try:
        ops = port_enterprise.operations
        if request.method == "GET":
            port_id = request.rel_url.query.get("port_id")
            if port_id:
                return json_response(ops.turnaround_analytics(port_id))
            return json_response(ops.status())
        body = await _read_json(request)
        action = body.get("action", "arrival")
        if action == "departure":
            return json_response(
                ops.plan_departure(
                    vessel_id=body.get("vessel_id", ""),
                    port_id=body.get("port_id", ""),
                    etd=body.get("etd", ""),
                ),
                status=201,
            )
        if action == "dock":
            return json_response(
                ops.schedule_dock(
                    dock_id=body.get("dock_id", ""),
                    vessel_id=body.get("vessel_id", ""),
                    window_start=body.get("window_start", ""),
                    window_end=body.get("window_end", ""),
                ),
                status=201,
            )
        if action == "berth":
            return json_response(
                ops.allocate_berth(berth_id=body.get("berth_id", ""), vessel_id=body.get("vessel_id", "")),
                status=201,
            )
        if action == "load":
            return json_response(
                ops.enqueue_loading(
                    cargo_id=body.get("cargo_id", ""),
                    vessel_id=body.get("vessel_id", ""),
                    priority=int(body.get("priority", 5) or 5),
                ),
                status=201,
            )
        if action == "unload":
            return json_response(
                ops.enqueue_unloading(
                    cargo_id=body.get("cargo_id", ""),
                    vessel_id=body.get("vessel_id", ""),
                    priority=int(body.get("priority", 5) or 5),
                ),
                status=201,
            )
        return json_response(
            ops.plan_arrival(
                vessel_id=body.get("vessel_id", ""),
                port_id=body.get("port_id", ""),
                eta=body.get("eta", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = port_enterprise.dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "port")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "port")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = port_enterprise.knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "port"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
