"""API handlers — Container Management (Sprint 15.2)."""

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
    return port_enterprise.container_management


async def cm_health_handler(request: web.Request) -> web.Response:
    health = port_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "container_platform_ready": health.get("container_platform_ready"),
            "yard_automation_ready": health.get("yard_automation_ready"),
            "port_equipment_ready": health.get("port_equipment_ready"),
            "digital_twin_ready": health.get("digital_twin_ready"),
            "terminal_automation_ready": health.get("terminal_automation_ready"),
            "suite": _suite().status(),
        }
    )


async def cm_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cm_containers_handler(request: web.Request) -> web.Response:
    try:
        containers = _suite().containers
        if request.method == "GET":
            cid = request.rel_url.query.get("container_id")
            if cid:
                return json_response({"history": containers.history(cid)})
            return json_response(containers.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "status":
            return json_response(
                containers.set_status(body.get("container_id", ""), status=body.get("status", "empty")),
                status=201,
            )
        if action == "inspect":
            return json_response(
                containers.inspect(
                    body.get("container_id", ""),
                    result=body.get("result", "pass"),
                    notes=body.get("notes", ""),
                ),
                status=201,
            )
        if action == "maintain":
            return json_response(
                containers.maintain(body.get("container_id", ""), work=body.get("work", "")),
                status=201,
            )
        return json_response(
            containers.register(
                container_number=body.get("container_number", ""),
                iso_type=body.get("iso_type", "40HC"),
                owner=body.get("owner", ""),
                status=body.get("status", "empty"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_operations_handler(request: web.Request) -> web.Response:
    try:
        ops = _suite().operations
        if request.method == "GET":
            return json_response(ops.status())
        body = await _read_json(request)
        action = body.get("action", "gate_in")
        cid = body.get("container_id", "")
        if action == "gate_out":
            return json_response(ops.gate_out(cid, gate=body.get("gate", "G1")), status=201)
        if action == "load":
            return json_response(ops.load(cid, vessel_id=body.get("vessel_id", "")), status=201)
        if action == "unload":
            return json_response(ops.unload(cid, vessel_id=body.get("vessel_id", "")), status=201)
        if action == "transship":
            return json_response(
                ops.transship(
                    cid,
                    from_vessel=body.get("from_vessel", ""),
                    to_vessel=body.get("to_vessel", ""),
                ),
                status=201,
            )
        if action == "transfer":
            return json_response(
                ops.transfer(cid, from_slot=body.get("from_slot", ""), to_slot=body.get("to_slot", "")),
                status=201,
            )
        if action == "reserve":
            return json_response(ops.reserve(cid, party=body.get("party", "")), status=201)
        return json_response(ops.gate_in(cid, gate=body.get("gate", "G1")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cm_yard_handler(request: web.Request) -> web.Response:
    try:
        yard = _suite().yard
        if request.method == "GET":
            yid = request.rel_url.query.get("yard_id")
            if yid and request.rel_url.query.get("view") == "capacity":
                return json_response(yard.capacity(yid))
            cn = request.rel_url.query.get("container_number")
            cid = request.rel_url.query.get("container_id")
            if cn or cid:
                return json_response({"results": yard.search(container_number=cn or "", container_id=cid or "")})
            return json_response(yard.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "block":
            return json_response(
                yard.create_block(
                    yard_id=body.get("yard_id", ""),
                    name=body.get("name", ""),
                    rows=int(body.get("rows", 10) or 10),
                    tiers=int(body.get("tiers", 5) or 5),
                ),
                status=201,
            )
        if action == "slot":
            return json_response(
                yard.allocate_slot(
                    block_id=body.get("block_id", ""),
                    row=int(body.get("row", 1) or 1),
                    bay=int(body.get("bay", 1) or 1),
                    tier=int(body.get("tier", 1) or 1),
                    container_id=body.get("container_id", ""),
                ),
                status=201,
            )
        if action == "optimize":
            return json_response(yard.optimize(body.get("yard_id", "")), status=201)
        return json_response(
            yard.register_yard(
                name=body.get("name", ""), capacity_teu=float(body.get("capacity_teu", 10000) or 10000)
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_equipment_handler(request: web.Request) -> web.Response:
    try:
        equipment = _suite().equipment
        if request.method == "GET":
            return json_response(equipment.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "health":
            return json_response(
                equipment.health(
                    body.get("equipment_id", ""), health_score=float(body.get("health_score", 90) or 90)
                ),
                status=201,
            )
        if action == "maintain":
            return json_response(
                equipment.schedule_maintenance(
                    body.get("equipment_id", ""),
                    due_at=body.get("due_at", ""),
                    work=body.get("work", "service"),
                ),
                status=201,
            )
        return json_response(
            equipment.register(
                name=body.get("name", ""),
                equipment_type=body.get("equipment_type", "sts"),
                yard_id=body.get("yard_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_automation_handler(request: web.Request) -> web.Response:
    try:
        automation = _suite().automation
        if request.method == "GET":
            return json_response(automation.status())
        body = await _read_json(request)
        action = body.get("action", "assign")
        if action == "dispatch":
            return json_response(
                automation.dispatch(body.get("equipment_id", ""), destination=body.get("destination", "")),
                status=201,
            )
        if action == "route":
            path = body.get("path") if isinstance(body.get("path"), list) else None
            return json_response(
                automation.route_container(container_id=body.get("container_id", ""), path=path),
                status=201,
            )
        if action == "yard_ai":
            return json_response(automation.optimize_yard_ai(body.get("yard_id", "")), status=201)
        if action == "queue":
            return json_response(
                automation.optimize_queue(
                    queue_name=body.get("queue_name", ""), depth=int(body.get("depth", 0) or 0)
                ),
                status=201,
            )
        if action == "energy":
            return json_response(automation.optimize_energy(equipment_id=body.get("equipment_id", "")), status=201)
        return json_response(
            automation.assign_task(
                equipment_id=body.get("equipment_id", ""),
                container_id=body.get("container_id", ""),
                task_type=body.get("task_type", "move"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_twin_handler(request: web.Request) -> web.Response:
    try:
        twin = _suite().twin
        if request.method == "GET":
            return json_response(twin.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        tid = body.get("twin_id", "")
        if action == "equipment":
            return json_response(twin.visualize_equipment(tid), status=201)
        if action == "containers":
            return json_response(twin.visualize_containers(tid), status=201)
        if action == "live":
            return json_response(twin.live_yard(tid), status=201)
        if action == "simulate":
            return json_response(twin.simulate(tid, hours=int(body.get("hours", 24) or 24)), status=201)
        if action == "forecast":
            return json_response(twin.forecast_capacity(tid, days=int(body.get("days", 7) or 7)), status=201)
        return json_response(
            twin.create_twin(terminal_name=body.get("terminal_name", ""), yard_id=body.get("yard_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "container")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "container")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "container"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
