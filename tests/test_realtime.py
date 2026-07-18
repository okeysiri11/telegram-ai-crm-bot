"""Tests — Platform Realtime Core."""

from __future__ import annotations

import asyncio
import json
import time
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import publish, reset_subscribers
from events.request_events import RequestCreatedEvent
from platform_management.management_router import register_management_routes
from platform_identity.models import AuthMethod, PlatformRole, Principal
from platform_management.permissions import ManagementRole
from platform_realtime.channel_manager import ChannelManager
from platform_realtime.connection_manager import connection_manager
from platform_realtime.event_dispatcher import (
    RealtimeEventDispatcher,
    register_realtime_event_handlers,
    reset_realtime_event_handlers,
)
from platform_realtime.heartbeat import PONG_TIMEOUT_SECONDS, heartbeat_manager
from platform_realtime.models import ClientConnection, RealtimeMessage
from platform_realtime.realtime_hub import realtime_hub
from platform_realtime.subscription_manager import subscription_manager


class MockWebSocket:
    def __init__(self) -> None:
        self.closed = False
        self.sent: list[str] = []

    async def send_str(self, payload: str) -> None:
        self.sent.append(payload)

    async def close(self, code: int = 1000, message: bytes = b"") -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def _reset_realtime():
    connection_manager.reset()
    subscription_manager.reset()
    realtime_hub.reset()
    heartbeat_manager._running = False
    heartbeat_manager._task = None
    yield
    connection_manager.reset()
    subscription_manager.reset()
    realtime_hub.reset()


@pytest.fixture
def mock_ws():
    return MockWebSocket()


@pytest.fixture
async def owner_connection(mock_ws):
    conn = ClientConnection.new(
        mock_ws,
        user_telegram_id=42,
        role=ManagementRole.OWNER.value,
        ip="127.0.0.1",
    )
    await connection_manager.add(conn)
    return conn


@pytest.fixture
async def readonly_connection(mock_ws):
    ws = MockWebSocket()
    conn = ClientConnection.new(
        ws,
        user_telegram_id=99,
        role=ManagementRole.READ_ONLY.value,
        ip="127.0.0.1",
    )
    await connection_manager.add(conn)
    return conn


@pytest.fixture
def owner_principal():
    return Principal(
        principal_id="telegram:42",
        auth_method=AuthMethod.TELEGRAM_OWNER,
        roles=[PlatformRole.OWNER.value],
        permissions=[],
        telegram_id=42,
    )


@pytest.fixture
def readonly_principal():
    return Principal(
        principal_id="telegram:99",
        auth_method=AuthMethod.TELEGRAM_USER,
        roles=[PlatformRole.READ_ONLY.value],
        permissions=[],
        telegram_id=99,
    )


@pytest.mark.asyncio
async def test_channel_permissions_matrix():
    matrix = ChannelManager.permission_matrix()
    assert matrix["dashboard"]["readonly"] is True
    assert matrix["configuration"]["readonly"] is False
    assert matrix["configuration"]["administrator"] is True
    assert matrix["ai"]["owner"] is True


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe(owner_connection, owner_principal):
    subscribed = await realtime_hub.subscribe(
        owner_connection.connection_id,
        ["dashboard", "requests", "system"],
        principal=owner_principal,
    )
    assert subscribed == ["dashboard", "requests", "system"]
    assert "dashboard" in owner_connection.subscribed_channels

    removed = await realtime_hub.unsubscribe(owner_connection.connection_id, ["requests"])
    assert removed == ["requests"]
    assert "requests" not in owner_connection.subscribed_channels


@pytest.mark.asyncio
async def test_subscribe_denied_for_readonly_on_configuration(readonly_connection, readonly_principal):
    from platform_realtime.exceptions import RealtimePermissionError

    with pytest.raises(RealtimePermissionError):
        await realtime_hub.subscribe(
            readonly_connection.connection_id,
            ["configuration"],
            principal=readonly_principal,
        )


@pytest.mark.asyncio
async def test_broadcast_channel_delivers_to_subscribers(owner_connection, mock_ws, owner_principal):
    await realtime_hub.subscribe(
        owner_connection.connection_id,
        ["dashboard"],
        principal=owner_principal,
    )

    other_ws = MockWebSocket()
    other = ClientConnection.new(other_ws, user_telegram_id=43, role="owner", ip="127.0.0.1")
    await connection_manager.add(other)

    message = RealtimeMessage(
        type="event",
        channel="dashboard",
        event="KPIUpdated",
        data={"value": 42},
    )
    sent = await realtime_hub.broadcast_channel("dashboard", message)
    assert sent == 1
    assert len(mock_ws.sent) == 1
    payload = json.loads(mock_ws.sent[0])
    assert payload["event"] == "KPIUpdated"
    assert payload["data"]["value"] == 42
    assert other_ws.sent == []


@pytest.mark.asyncio
async def test_broadcast_user(owner_connection, mock_ws):
    message = RealtimeMessage(type="event", event="Direct", data={"ok": True})
    sent = await realtime_hub.broadcast_user(42, message)
    assert sent == 1
    assert json.loads(mock_ws.sent[0])["event"] == "Direct"


@pytest.mark.asyncio
async def test_broadcast_all_connections(owner_connection, mock_ws):
    message = RealtimeMessage(type="event", event="Global", data={})
    sent = await realtime_hub.broadcast(message)
    assert sent == 1
    assert mock_ws.sent


@pytest.mark.asyncio
async def test_disconnect_cleans_subscriptions(owner_connection, owner_principal):
    await realtime_hub.subscribe(
        owner_connection.connection_id,
        ["dashboard"],
        principal=owner_principal,
    )
    await realtime_hub.disconnect(owner_connection.connection_id)
    subs = await subscription_manager.subscriptions_snapshot()
    assert subs == {}


@pytest.mark.asyncio
async def test_heartbeat_stale_disconnect(owner_connection, mock_ws):
    owner_connection.last_pong = time.monotonic() - PONG_TIMEOUT_SECONDS - 1
    await heartbeat_manager._tick(realtime_hub)
    assert mock_ws.closed is True
    assert await connection_manager.connected_client_count() == 0


@pytest.mark.asyncio
async def test_event_dispatcher_routes_request_created(owner_principal):
    reset_subscribers()
    reset_realtime_event_handlers()
    register_realtime_event_handlers()
    await realtime_hub.subscribe(
        (await _add_conn()).connection_id,
        ["requests", "dashboard"],
        principal=owner_principal,
    )

    widget_payload = {"meta": {"widget_id": "active_requests"}, "data": {"total": 1}}

    with patch(
        "platform_operations.dashboard_service.operations_dashboard_service.fetch_widget",
        new_callable=AsyncMock,
        return_value=type("W", (), {"to_dict": lambda self: widget_payload})(),
    ):
        event = RequestCreatedEvent(
            request_id="r1",
            request_number="REQ-1",
            vertical="auto",
            request_type="lead",
        )
        await RealtimeEventDispatcher.handle(event)

    subs = await subscription_manager.subscribers("requests")
    assert len(subs) == 1


async def _add_conn() -> ClientConnection:
    ws = MockWebSocket()
    conn = ClientConnection.new(ws, user_telegram_id=7, role="owner", ip="127.0.0.1")
    await connection_manager.add(conn)
    return conn


@pytest.mark.asyncio
async def test_event_bus_to_realtime_integration(owner_principal):
    reset_subscribers()
    reset_realtime_event_handlers()
    register_realtime_event_handlers()

    ws = MockWebSocket()
    conn = ClientConnection.new(ws, user_telegram_id=7, role="owner", ip="127.0.0.1")
    await connection_manager.add(conn)
    await realtime_hub.subscribe(conn.connection_id, ["requests"], principal=owner_principal)

    with patch(
        "platform_operations.dashboard_service.operations_dashboard_service.fetch_widget",
        new_callable=AsyncMock,
        return_value=type("W", (), {"to_dict": lambda self: {"data": {}}})(),
    ):
        await publish(
            RequestCreatedEvent(
                request_id="r2",
                request_number="REQ-2",
                vertical="auto",
                request_type="lead",
            ),
            wait=True,
        )

    assert any("RequestCreatedEvent" in msg for msg in ws.sent)


@pytest.mark.asyncio
async def test_management_realtime_endpoint(owner_principal, auth_headers):
    app = web.Application()
    register_management_routes(app)

    async def _owner(_tid):
        return ManagementRole.OWNER

    with patch("platform_management.permissions.resolve_role", _owner), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        ws = MockWebSocket()
        conn = ClientConnection.new(ws, user_telegram_id=42, role="owner", ip="127.0.0.1")
        await connection_manager.add(conn)
        await realtime_hub.subscribe(conn.connection_id, ["dashboard"], principal=owner_principal)

        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/realtime", headers=auth_headers)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            data = body["data"]
            assert "connections" in data
            assert "subscriptions" in data
            assert "channels" in data
            assert "statistics" in data
            assert len(data["connections"]) == 1


@pytest.mark.asyncio
async def test_performance_1000_broadcasts(owner_principal):
    """Hub should fan-out to 1000 subscribers with single payload serialization."""
    connections: list[ClientConnection] = []
    for i in range(1000):
        ws = MockWebSocket()
        conn = ClientConnection.new(ws, user_telegram_id=1000 + i, role="owner", ip="127.0.0.1")
        await connection_manager.add(conn)
        await realtime_hub.subscribe(conn.connection_id, ["dashboard"], principal=owner_principal)
        connections.append(conn)

    message = RealtimeMessage(type="event", event="LoadTest", data={"n": 1000})
    started = time.perf_counter()
    sent = await realtime_hub.broadcast_channel("dashboard", message)
    elapsed_ms = (time.perf_counter() - started) * 1000

    assert sent == 1000
    assert elapsed_ms < 5000
    first_payload = connections[0].ws.sent[0]
    assert all(conn.ws.sent[0] == first_payload for conn in connections[:50])


@pytest.mark.asyncio
async def test_reconnect_count_on_rapid_reconnect():
    ws1 = MockWebSocket()
    conn1 = ClientConnection.new(ws1, user_telegram_id=555, role="owner", ip="127.0.0.1")
    await connection_manager.add(conn1)
    await realtime_hub.disconnect(conn1.connection_id)

    ws2 = MockWebSocket()
    conn2 = ClientConnection.new(ws2, user_telegram_id=555, role="owner", ip="127.0.0.1")
    added = await connection_manager.add(conn2)
    assert added.reconnect_count == 1
