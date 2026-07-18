# Realtime Hub — central publisher for WebSocket clients.

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from aiohttp import web

from platform_realtime.connection_manager import connection_manager
from platform_realtime.models import RealtimeMessage, RealtimeMetrics
from platform_realtime.subscription_manager import subscription_manager

logger = logging.getLogger(__name__)

class RealtimeHub:
    """Broadcasts operational state to subscribed WebSocket clients."""

    def __init__(self) -> None:
        self.metrics = RealtimeMetrics()
        self._lock = asyncio.Lock()
        self._payload_cache: dict[str, str] = {}

    async def subscribe(
        self,
        connection_id: str,
        channels: list[str],
        *,
        principal,
    ) -> list[str]:
        from platform_identity.models import Principal

        if not isinstance(principal, Principal):
            from platform_identity.identity_service import identity_service

            if isinstance(principal, int):
                principal = await identity_service.authenticate_telegram(principal)
            elif hasattr(principal, "value"):
                principal = await identity_service.authenticate_telegram(
                    (await connection_manager.get(connection_id)).user_telegram_id
                )
        return await subscription_manager.subscribe(connection_id, channels, principal=principal)

    async def unsubscribe(self, connection_id: str, channels: list[str]) -> list[str]:
        return await subscription_manager.unsubscribe(connection_id, channels)

    async def broadcast(self, message: RealtimeMessage) -> int:
        """Send to every connected client."""
        connections = await connection_manager.list_connections()
        return await self._deliver([conn.connection_id for conn in connections], message)

    async def broadcast_channel(self, channel: str, message: RealtimeMessage) -> int:
        """Send to all subscribers of a channel."""
        message.channel = channel
        connection_ids = await subscription_manager.subscribers(channel)
        return await self._deliver(list(connection_ids), message)

    async def broadcast_user(self, user_telegram_id: int, message: RealtimeMessage) -> int:
        """Send to all connections for a specific user."""
        connections = await connection_manager.connections_for_user(user_telegram_id)
        return await self._deliver([conn.connection_id for conn in connections], message)

    async def send_raw(self, connection_id: str, payload: str) -> bool:
        try:
            connection = await connection_manager.get(connection_id)
        except Exception:
            return False

        if connection.ws.closed:
            await self.disconnect(connection_id, reason="socket_closed")
            return False

        try:
            await connection.ws.send_str(payload)
            self.metrics.record_message()
            return True
        except Exception:
            logger.warning("realtime_send_failed id=%s", connection_id, exc_info=True)
            self.metrics.record_drop()
            await self.disconnect(connection_id, reason="send_failed")
            return False

    async def disconnect(self, connection_id: str, *, reason: str = "closed") -> None:
        try:
            connection = await connection_manager.get(connection_id)
        except Exception:
            return

        if not connection.ws.closed:
            try:
                await connection.ws.close(code=4000, message=reason.encode("utf-8")[:120])
            except Exception:
                pass

        await subscription_manager.remove_connection(connection_id)
        removed = await connection_manager.remove(connection_id)
        if removed is not None and removed.reconnect_count > 0:
            self.metrics.record_reconnect()

    async def _deliver(self, connection_ids: list[str], message: RealtimeMessage) -> int:
        if not connection_ids:
            return 0

        self.metrics.record_event()
        cache_key = self._cache_key(message)
        payload = self._payload_cache.get(cache_key)
        if payload is None:
            payload = json.dumps(message.to_dict(), default=str)
            self._payload_cache[cache_key] = payload
            if len(self._payload_cache) > 256:
                self._payload_cache.clear()

        sent = 0
        for connection_id in connection_ids:
            if await self.send_raw(connection_id, payload):
                sent += 1
        return sent

    @staticmethod
    def _cache_key(message: RealtimeMessage) -> str:
        return f"{message.type}:{message.channel}:{message.event}:{message.widget_id}:{message.event_id}"

    async def status(self) -> dict[str, Any]:
        from platform_realtime.channel_manager import ChannelManager
        from platform_realtime.presence import presence_tracker

        self.metrics.connected_clients = await connection_manager.connected_client_count()
        self.metrics.connected_users = await connection_manager.connected_user_count()

        connections = await connection_manager.list_connections()
        subscriptions = await subscription_manager.subscriptions_snapshot()

        return {
            "connections": [conn.to_dict() for conn in connections],
            "subscriptions": subscriptions,
            "channels": ChannelManager.list_channels(),
            "permission_matrix": ChannelManager.permission_matrix(),
            "presence": await presence_tracker.snapshot(),
            "statistics": self.metrics.to_dict(),
        }

    def reset(self) -> None:
        self.metrics = RealtimeMetrics()
        self._payload_cache.clear()


realtime_hub = RealtimeHub()
