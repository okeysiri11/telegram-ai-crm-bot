"""Enterprise Event Bus HTTP + WebSocket API — Sprint 36.1.

Primary: /api/event-bus/*
Also: /management/v1/event-bus/* (+ legacy /management/event-bus/*)
WebSocket: /api/event-bus/ws
"""

from __future__ import annotations

import asyncio
import json
import logging

from aiohttp import WSMsgType, web

from platform_enterprise_event_bus.service import enterprise_event_bus_service as eeb
from platform_management.permissions import ManagementRole, require_role

logger = logging.getLogger(__name__)


def _actor(request: web.Request) -> str:
    return (
        request.headers.get("X-Actor-Id")
        or request.get("user_id")
        or request.query.get("actor")
        or "system"
    )


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def eb_status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": eeb.status()})


@require_role(ManagementRole.READ_ONLY)
async def eb_topics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": {"topics": eeb.list_topics()}})


@require_role(ManagementRole.ADMINISTRATOR)
async def eb_topics_create_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        topic = eeb.create_topic(str(body["name"]), description=str(body.get("description") or ""))
    except (KeyError, ValueError) as exc:
        return _error(exc, status=409 if isinstance(exc, ValueError) else 400)
    return web.json_response({"success": True, "data": topic}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def eb_events_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    events = eeb.list_events(
        topic=request.query.get("topic"),
        event_type=request.query.get("event_type"),
        tenant_id=request.query.get("tenant_id"),
        source_service=request.query.get("source_service"),
        limit=limit,
    )
    return web.json_response({"success": True, "data": {"events": events, "count": len(events)}})


@require_role(ManagementRole.READ_ONLY)
async def eb_event_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = eeb.inspect(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def eb_publish_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        result = await eeb.publish(body, actor=_actor(request))
    except ValueError as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": result}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def eb_subscribe_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        sub = eeb.subscribe(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": sub}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def eb_unsubscribe_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json() if request.body_exists else {}
    try:
        data = eeb.unsubscribe(payload=body)
    except ValueError as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def eb_replay_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await eeb.replay(body, actor=_actor(request))
    except KeyError as exc:
        return _error(exc, status=404)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def eb_statistics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": eeb.statistics()})


@require_role(ManagementRole.READ_ONLY)
async def eb_traffic_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": eeb.traffic()})


@require_role(ManagementRole.READ_ONLY)
async def eb_dead_letter_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    return web.json_response({"success": True, "data": {"items": eeb.dead_letter(limit=limit)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def eb_retry_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await eeb.retry(body, actor=_actor(request))
    except (KeyError, ValueError) as exc:
        status = 404 if isinstance(exc, KeyError) else 400
        return _error(exc, status=status)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def eb_subscribers_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": {"subscribers": eeb.list_subscribers()}})


async def eb_websocket_handler(request: web.Request) -> web.WebSocketResponse:
    """Live event stream WebSocket — /api/event-bus/ws."""
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)
    queue: asyncio.Queue = asyncio.Queue(maxsize=500)

    async def _listener(event) -> None:
        try:
            queue.put_nowait(event.to_dict())
        except asyncio.QueueFull:
            pass

    eeb.bus.add_live_listener(_listener)
    await ws.send_json({"type": "welcome", "channel": "event_bus", "status": eeb.status()})

    async def _pump() -> None:
        while not ws.closed:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=1.0)
                await ws.send_json({"type": "event", "data": item})
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

    pump = asyncio.create_task(_pump())
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    payload = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue
                if payload.get("type") == "ping":
                    await ws.send_json({"type": "pong"})
                elif payload.get("type") == "subscribe":
                    await ws.send_json({"type": "subscribed", "filters": payload.get("filters") or {}})
            elif msg.type in {WSMsgType.CLOSE, WSMsgType.ERROR}:
                break
    finally:
        pump.cancel()
        if _listener in eeb.bus._live_listeners:
            eeb.bus._live_listeners.remove(_listener)
        if not ws.closed:
            await ws.close()
    return ws


ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", eb_status_handler),
    ("GET", "topics", eb_topics_handler),
    ("POST", "topics", eb_topics_create_handler),
    ("GET", "events", eb_events_handler),
    ("GET", "events/{id}", eb_event_get_handler),
    ("POST", "publish", eb_publish_handler),
    ("POST", "subscribe", eb_subscribe_handler),
    ("POST", "unsubscribe", eb_unsubscribe_handler),
    ("POST", "replay", eb_replay_handler),
    ("GET", "statistics", eb_statistics_handler),
    ("GET", "traffic", eb_traffic_handler),
    ("GET", "dead-letter", eb_dead_letter_handler),
    ("POST", "retry", eb_retry_handler),
    ("GET", "subscribers", eb_subscribers_handler),
]


def register_enterprise_event_bus_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/event-bus",
        legacy_prefix="/management/event-bus",
    )

    for method, rel, handler in ROUTE_SPECS:
        rel = rel.strip("/")
        path = f"/api/event-bus/{rel}" if rel else "/api/event-bus"
        getattr(app.router, f"add_{method.lower()}")(path, handler)

    app.router.add_get("/api/event-bus/ws", eb_websocket_handler)
    app.router.add_get(f"{MANAGEMENT_V1_PREFIX}/event-bus/ws", eb_websocket_handler)
