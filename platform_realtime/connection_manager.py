# Connected WebSocket client registry.

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict

from platform_realtime.exceptions import ConnectionNotFoundError
from platform_realtime.models import ClientConnection

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, ClientConnection] = {}
        self._by_user: dict[int, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._recent_disconnects: dict[int, float] = {}

    async def add(self, connection: ClientConnection) -> ClientConnection:
        async with self._lock:
            reconnect_count = 0
            last_disconnect = self._recent_disconnects.get(connection.user_telegram_id)
            if last_disconnect is not None and time.monotonic() - last_disconnect < 300:
                reconnect_count = 1
            connection.reconnect_count = reconnect_count
            self._connections[connection.connection_id] = connection
            self._by_user[connection.user_telegram_id].add(connection.connection_id)
        logger.info(
            "realtime_client_connected id=%s user=%s role=%s",
            connection.connection_id,
            connection.user_telegram_id,
            connection.role,
        )
        return connection

    async def remove(self, connection_id: str) -> ClientConnection | None:
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            if connection is None:
                return None
            user_bucket = self._by_user.get(connection.user_telegram_id)
            if user_bucket is not None:
                user_bucket.discard(connection_id)
                if not user_bucket:
                    del self._by_user[connection.user_telegram_id]
            self._recent_disconnects[connection.user_telegram_id] = time.monotonic()
        logger.info("realtime_client_disconnected id=%s user=%s", connection_id, connection.user_telegram_id)
        return connection

    async def get(self, connection_id: str) -> ClientConnection:
        async with self._lock:
            connection = self._connections.get(connection_id)
        if connection is None:
            raise ConnectionNotFoundError(f"Connection {connection_id} not found")
        return connection

    async def list_connections(self) -> list[ClientConnection]:
        async with self._lock:
            return list(self._connections.values())

    async def connections_for_user(self, user_telegram_id: int) -> list[ClientConnection]:
        async with self._lock:
            ids = list(self._by_user.get(user_telegram_id, ()))
            return [self._connections[cid] for cid in ids if cid in self._connections]

    async def touch_ping(self, connection_id: str) -> None:
        connection = await self.get(connection_id)
        connection.last_ping = time.monotonic()

    async def touch_pong(self, connection_id: str) -> None:
        connection = await self.get(connection_id)
        connection.last_pong = time.monotonic()

    async def connected_user_count(self) -> int:
        async with self._lock:
            return len(self._by_user)

    async def connected_client_count(self) -> int:
        async with self._lock:
            return len(self._connections)

    async def stale_connections(self, *, pong_timeout_seconds: float) -> list[ClientConnection]:
        now = time.monotonic()
        async with self._lock:
            return [
                conn
                for conn in self._connections.values()
                if now - conn.last_pong > pong_timeout_seconds
            ]

    def reset(self) -> None:
        self._connections.clear()
        self._by_user.clear()
        self._recent_disconnects.clear()


connection_manager = ConnectionManager()
