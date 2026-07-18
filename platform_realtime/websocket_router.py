# WebSocket router — client protocol and route registration.

from __future__ import annotations

import json
import logging

from aiohttp import web

from platform_management.permissions import ManagementRole, resolve_role
from platform_realtime.connection_manager import connection_manager
from platform_realtime.event_dispatcher import register_realtime_event_handlers
from platform_realtime.heartbeat import heartbeat_manager
from platform_realtime.models import ClientConnection, RealtimeMessage
from platform_realtime.realtime_hub import realtime_hub

logger = logging.getLogger(__name__)

_realtime_started = False


def _client_ip(request: web.Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    peer = request.transport.get_extra_info("peername") if request.transport else None
    return peer[0] if peer else "unknown"


def _parse_actor_id(request: web.Request) -> int | None:
    raw = request.headers.get("X-Actor-Telegram-Id") or request.query.get("actor_telegram_id")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    actor_id = _parse_actor_id(request)
    if actor_id is None:
        raise web.HTTPUnauthorized(text="X-Actor-Telegram-Id required")

    try:
        role = await resolve_role(actor_id)
    except Exception as exc:
        raise web.HTTPForbidden(text=str(exc)) from exc

    ws = web.WebSocketResponse(autoping=True, heartbeat=30)
    await ws.prepare(request)

    connection = ClientConnection.new(
        ws,
        user_telegram_id=actor_id,
        role=role.value,
        ip=_client_ip(request),
    )
    await connection_manager.add(connection)

    welcome = RealtimeMessage(
        type="connected",
        event="Connected",
        data={
            "connection_id": connection.connection_id,
            "role": role.value,
            "channels_available": _channels_for_role(role),
            "heartbeat_interval_seconds": 30,
            "reconnect": True,
        },
    )
    await ws.send_str(json.dumps(welcome.to_dict(), default=str))

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await _handle_client_message(connection, role, msg.data)
            elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.CLOSED, web.WSMsgType.ERROR):
                break
    finally:
        await realtime_hub.disconnect(connection.connection_id, reason="client_closed")

    return ws


async def _handle_client_message(
    connection: ClientConnection,
    role: ManagementRole,
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
                actor_role=role,
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


def _channels_for_role(role: ManagementRole) -> list[str]:
    from platform_realtime.channel_manager import ChannelManager

    return [
        channel
        for channel in ChannelManager.list_channels()
        if ChannelManager.can_subscribe(role, channel)
    ]


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
    prefix = "/management"
    app.router.add_get(f"{prefix}/realtime/ws", websocket_handler)
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    logger.info("realtime_websocket_route_registered path=%s/realtime/ws", prefix)
