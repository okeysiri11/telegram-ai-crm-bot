"""API handlers — AI Operating System (Sprint 12.4)."""

from __future__ import annotations

from aiohttp import web

from applications.ai_os import ai_os
from applications.ai_os.api.middleware import json_response
from applications.ai_os.shared.exceptions import NotFoundError, ValidationError


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
    return json_response(ai_os.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(ai_os.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def kernel_handler(request: web.Request) -> web.Response:
    try:
        kernel = ai_os.kernel
        if request.method == "GET":
            return json_response({"schedulers": kernel.list_schedulers(), "status": kernel.status()})
        body = await _read_json(request)
        action = body.get("action", "schedule")
        if action == "boot":
            return json_response(kernel.boot(), status=201)
        if action == "tick":
            return json_response(kernel.tick(body.get("scheduler", "task")))
        return json_response(
            kernel.schedule(
                scheduler=body.get("scheduler", "task"),
                payload=body.get("payload"),
                priority=int(body.get("priority", 5)),
                name=body.get("name", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def process_handler(request: web.Request) -> web.Response:
    try:
        pm = ai_os.processes
        if request.method == "GET":
            return json_response({"processes": pm.list_processes(), "status": pm.status()})
        body = await _read_json(request)
        action = body.get("action", "start")
        if action == "enqueue":
            return json_response(pm.enqueue(queue=body.get("queue", "default"), item=body.get("item"), priority=bool(body.get("priority", False))), status=201)
        if action == "dequeue":
            item = pm.dequeue(queue=body.get("queue", "default"))
            return json_response({"item": item})
        if action == "lifecycle":
            return json_response(pm.lifecycle(body.get("process_id", ""), action=body.get("lifecycle_action", "stop")))
        if action == "health":
            return json_response(pm.health_monitor(body.get("process_id", ""), healthy=bool(body.get("healthy", True)), detail=body.get("detail", "")))
        return json_response(
            pm.start_process(name=body.get("name", ""), kind=body.get("kind", "ai_process"), priority=int(body.get("priority", 5)), metadata=body.get("metadata")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bus_handler(request: web.Request) -> web.Response:
    try:
        bus = ai_os.bus
        if request.method == "GET":
            return json_response({
                "catalog": bus.catalog(),
                "messages": bus.subscribe_poll(bus=request.rel_url.query.get("bus", "event"), topic=request.rel_url.query.get("topic")),
            })
        body = await _read_json(request)
        return json_response(
            bus.publish(bus=body.get("bus", "event"), topic=body.get("topic", ""), payload=body.get("payload"), source=body.get("source", "api")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def memory_handler(request: web.Request) -> web.Response:
    try:
        mem = ai_os.memory
        if request.method == "GET":
            tier = request.rel_url.query.get("tier", "global")
            key = request.rel_url.query.get("key")
            if key:
                return json_response(mem.get(tier=tier, key=key))
            return json_response({"tier": tier, "items": mem.list_tier(tier), "status": mem.status()})
        body = await _read_json(request)
        action = body.get("action", "put")
        if action == "clear":
            return json_response(mem.clear_tier(body.get("tier", "session")))
        return json_response(
            mem.put(tier=body.get("tier", "global"), key=body.get("key", ""), value=body.get("value"), ttl_s=body.get("ttl_s")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def runtime_handler(request: web.Request) -> web.Response:
    try:
        rt = ai_os.runtime
        body = await _read_json(request)
        action = body.get("action", "execute")
        if action == "context":
            return json_response(rt.create_context(name=body.get("name", "default"), data=body.get("data")), status=201)
        if action == "checkpoint":
            return json_response(rt.checkpoint(body.get("runtime_id", "")), status=201)
        if action == "recover":
            return json_response(rt.recover(body.get("runtime_id", ""), checkpoint_id=body.get("checkpoint_id")))
        if action == "state":
            return json_response(rt.state(body.get("runtime_id", "")))
        return json_response(
            rt.execute(
                name=body.get("name", "job"),
                payload=body.get("payload"),
                context_id=body.get("context_id", ""),
                sandboxed=bool(body.get("sandboxed", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def communication_handler(request: web.Request) -> web.Response:
    try:
        comm = ai_os.communication
        if request.method == "GET":
            return json_response({"inbox": comm.inbox(request.rel_url.query.get("recipient", "")), "status": comm.status()})
        body = await _read_json(request)
        return json_response(
            comm.send(
                channel=body.get("channel", "agent_to_agent"),
                sender=body.get("sender", ""),
                recipient=body.get("recipient", ""),
                body=body.get("body", ""),
                metadata=body.get("metadata"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def enterprise_handler(request: web.Request) -> web.Response:
    try:
        ent = ai_os.enterprise
        if request.method == "GET":
            return json_response(ent.status())
        body = await _read_json(request)
        action = body.get("action", "create_cluster")
        if action == "scale":
            return json_response(ent.scale(body.get("cluster_id", ""), nodes=int(body.get("nodes", 3))))
        if action == "failover":
            return json_response(ent.failover(body.get("cluster_id", ""), from_node=body.get("from_node", ""), to_node=body.get("to_node", "")))
        if action == "recover":
            return json_response(ent.disaster_recovery(body.get("cluster_id", "")))
        if action == "balance":
            return json_response(ent.load_balance(body.get("cluster_id", "")))
        return json_response(
            ent.create_cluster(name=body.get("name", ""), region=body.get("region", "global"), nodes=int(body.get("nodes", 3))),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def observability_handler(request: web.Request) -> web.Response:
    try:
        obs = ai_os.observability
        if request.method == "GET":
            return json_response({
                "health": obs.health_dashboard(),
                "performance": obs.performance_dashboard(),
                "status": obs.status(),
            })
        body = await _read_json(request)
        action = body.get("action", "log")
        if action == "metric":
            return json_response(obs.metric(name=body.get("name", ""), value=float(body.get("value", 0)), tags=body.get("tags")), status=201)
        if action == "trace":
            return json_response(obs.trace(name=body.get("name", ""), spans=body.get("spans")), status=201)
        if action == "alert":
            return json_response(obs.alert(severity=body.get("severity", "info"), message=body.get("message", ""), source=body.get("source", "api")), status=201)
        return json_response(obs.log(level=body.get("level", "info"), message=body.get("message", ""), source=body.get("source", "api")), status=201)
    except Exception as exc:
        return _handle_error(exc)
