# WebSocket router — IAM-authenticated realtime connections.

from __future__ import annotations

import json
import logging

from aiohttp import web

from platform_identity.identity_service import identity_service
from platform_identity.models import Principal
from platform_realtime.connection_manager import connection_manager
from platform_realtime.event_dispatcher import register_realtime_event_handlers
from platform_realtime.heartbeat import heartbeat_manager
from platform_realtime.models import ALL_CHANNELS, ClientConnection, RealtimeMessage
from platform_realtime.realtime_hub import realtime_hub

logger = logging.getLogger(__name__)

_realtime_started = False


def _client_ip(request: web.Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    peer = request.transport.get_extra_info("peername") if request.transport else None
    return peer[0] if peer else "unknown"


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    try:
        principal = await identity_service.authenticate_request(request)
    except Exception as exc:
        raise web.HTTPUnauthorized(text=str(exc)) from exc

    ws = web.WebSocketResponse(autoping=True, heartbeat=30)
    await ws.prepare(request)

    primary_role = principal.roles[0] if principal.roles else "readonly"
    connection = ClientConnection.new(
        ws,
        user_telegram_id=principal.telegram_id or 0,
        role=primary_role,
        ip=_client_ip(request),
    )
    await connection_manager.add(connection)

    welcome = RealtimeMessage(
        type="connected",
        event="Connected",
        data={
            "connection_id": connection.connection_id,
            "principal_id": principal.principal_id,
            "roles": principal.roles,
            "channels_available": await _channels_for_principal(principal),
            "heartbeat_interval_seconds": 30,
            "reconnect": True,
        },
    )
    await ws.send_str(json.dumps(welcome.to_dict(), default=str))

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await _handle_client_message(connection, principal, msg.data)
            elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.CLOSED, web.WSMsgType.ERROR):
                break
    finally:
        await realtime_hub.disconnect(connection.connection_id, reason="client_closed")

    return ws


async def _handle_client_message(
    connection: ClientConnection,
    principal: Principal,
    raw: str,
) -> None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        await _send_error(connection, "invalid_json")
        return

    msg_type = payload.get("type", "")
    if msg_type == "pong":
        await connection_manager.touch_pong(connection.connection_id)
        return

    if msg_type == "ping":
        await connection_manager.touch_pong(connection.connection_id)
        await realtime_hub.send_raw(
            connection.connection_id,
            json.dumps({"type": "pong", "timestamp": payload.get("timestamp")}),
        )
        return

    if msg_type == "subscribe":
        channels = payload.get("channels") or []
        try:
            subscribed = await realtime_hub.subscribe(
                connection.connection_id,
                channels,
                principal=principal,
            )
        except Exception as exc:
            await _send_error(connection, str(exc))
            return

        ack = RealtimeMessage(
            type="subscribed",
            event="Subscribed",
            data={"channels": subscribed},
        )
        await realtime_hub.send_raw(
            connection.connection_id,
            json.dumps(ack.to_dict(), default=str),
        )
        return

    if msg_type == "unsubscribe":
        channels = payload.get("channels") or []
        try:
            removed = await realtime_hub.unsubscribe(connection.connection_id, channels)
        except Exception as exc:
            await _send_error(connection, str(exc))
            return

        ack = RealtimeMessage(
            type="unsubscribed",
            event="Unsubscribed",
            data={"channels": removed},
        )
        await realtime_hub.send_raw(
            connection.connection_id,
            json.dumps(ack.to_dict(), default=str),
        )
        return

    await _send_error(connection, f"unknown_message_type:{msg_type}")


async def _send_error(connection: ClientConnection, error: str) -> None:
    message = RealtimeMessage(type="error", event="Error", data={"error": error})
    await realtime_hub.send_raw(
        connection.connection_id,
        json.dumps(message.to_dict(), default=str),
    )


async def _channels_for_principal(principal: Principal) -> list[str]:
    available: list[str] = []
    for channel in ALL_CHANNELS:
        if await identity_service.authorize_realtime_channel(principal, channel):
            available.append(channel)
    return available


async def _on_startup(app: web.Application) -> None:
    global _realtime_started
    if _realtime_started:
        return
    register_realtime_event_handlers()
    heartbeat_manager.start(realtime_hub)
    _realtime_started = True
    logger.info("realtime_core_started")


async def _on_cleanup(app: web.Application) -> None:
    await heartbeat_manager.stop()
    connections = await connection_manager.list_connections()
    for conn in connections:
        await realtime_hub.disconnect(conn.connection_id, reason="shutdown")


def register_realtime_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=[("GET", "realtime/ws", websocket_handler)],
        v1_prefix=MANAGEMENT_V1_PREFIX,
        legacy_prefix="/management",
    )
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    logger.info("realtime_websocket_route_registered v1=%s/realtime/ws", MANAGEMENT_V1_PREFIX)
