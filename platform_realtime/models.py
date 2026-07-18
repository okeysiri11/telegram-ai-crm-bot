# Realtime domain models — connections, messages, channels, metrics.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from aiohttp import web


class RealtimeChannel(str, enum.Enum):
    SYSTEM = "system"
    DASHBOARD = "dashboard"
    REQUESTS = "requests"
    WORKFLOWS = "workflows"
    MANAGERS = "managers"
    AUDIT = "audit"
    CONFIGURATION = "configuration"
    NOTIFICATIONS = "notifications"
    PLUGINS = "plugins"
    AI = "ai"
    HEALTH = "health"


ALL_CHANNELS: tuple[str, ...] = tuple(ch.value for ch in RealtimeChannel)


@dataclass
class ClientConnection:
    connection_id: str
    ws: web.WebSocketResponse
    user_telegram_id: int
    role: str
    ip: str
    connected_at: datetime
    last_ping: float = field(default_factory=time.monotonic)
    last_pong: float = field(default_factory=time.monotonic)
    reconnect_count: int = 0
    subscribed_channels: set[str] = field(default_factory=set)

    @staticmethod
    def new(
        ws: web.WebSocketResponse,
        *,
        user_telegram_id: int,
        role: str,
        ip: str,
        reconnect_count: int = 0,
    ) -> ClientConnection:
        now = time.monotonic()
        return ClientConnection(
            connection_id=str(uuid.uuid4()),
            ws=ws,
            user_telegram_id=user_telegram_id,
            role=role,
            ip=ip,
            connected_at=datetime.now(timezone.utc),
            last_ping=now,
            last_pong=now,
            reconnect_count=reconnect_count,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "user_telegram_id": self.user_telegram_id,
            "role": self.role,
            "ip": self.ip,
            "connected_at": self.connected_at.isoformat(),
            "last_ping": self.last_ping,
            "last_pong": self.last_pong,
            "reconnect_count": self.reconnect_count,
            "subscribed_channels": sorted(self.subscribed_channels),
        }


@dataclass
class RealtimeMessage:
    """Outbound realtime envelope — serialized once per broadcast."""

    type: str = "event"
    channel: str = ""
    event: str = ""
    widget_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "channel": self.channel,
            "event": self.event,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        if self.widget_id:
            payload["widget_id"] = self.widget_id
        if self.event_id:
            payload["event_id"] = self.event_id
        return payload


@dataclass
class RealtimeMetrics:
    connected_users: int = 0
    connected_clients: int = 0
    messages_sent: int = 0
    events_dispatched: int = 0
    dropped_messages: int = 0
    reconnects: int = 0
    messages_per_second: float = 0.0
    events_per_second: float = 0.0
    _window_started: float = field(default_factory=time.monotonic, repr=False)
    _window_messages: int = field(default=0, repr=False)
    _window_events: int = field(default=0, repr=False)

    def record_message(self, count: int = 1) -> None:
        self.messages_sent += count
        self._window_messages += count
        self._refresh_rates()

    def record_event(self) -> None:
        self.events_dispatched += 1
        self._window_events += 1
        self._refresh_rates()

    def record_drop(self, count: int = 1) -> None:
        self.dropped_messages += count

    def record_reconnect(self) -> None:
        self.reconnects += 1

    def _refresh_rates(self) -> None:
        elapsed = max(time.monotonic() - self._window_started, 0.001)
        if elapsed >= 1.0:
            self.messages_per_second = round(self._window_messages / elapsed, 2)
            self.events_per_second = round(self._window_events / elapsed, 2)
            self._window_started = time.monotonic()
            self._window_messages = 0
            self._window_events = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "connected_users": self.connected_users,
            "connected_clients": self.connected_clients,
            "messages_sent": self.messages_sent,
            "events_dispatched": self.events_dispatched,
            "dropped_messages": self.dropped_messages,
            "reconnects": self.reconnects,
            "messages_per_second": self.messages_per_second,
            "events_per_second": self.events_per_second,
        }
