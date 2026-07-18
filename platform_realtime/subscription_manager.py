# Per-connection channel subscriptions.

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from platform_management.permissions import ManagementRole
from platform_realtime.channel_manager import ChannelManager
from platform_realtime.connection_manager import connection_manager
from platform_realtime.exceptions import ConnectionNotFoundError, SubscriptionError

logger = logging.getLogger(__name__)


class SubscriptionManager:
    def __init__(self) -> None:
        self._channel_subscribers: dict[str, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(
        self,
        connection_id: str,
        channels: list[str],
        *,
        actor_role: ManagementRole,
    ) -> list[str]:
        if not channels:
            raise SubscriptionError("channels list is required")

        try:
            connection = await connection_manager.get(connection_id)
        except ConnectionNotFoundError as exc:
            raise SubscriptionError(str(exc)) from exc

        subscribed: list[str] = []
        async with self._lock:
            for channel in channels:
                normalized = ChannelManager.validate_channel(channel)
                ChannelManager.assert_can_subscribe(actor_role, normalized)
                connection.subscribed_channels.add(normalized)
                self._channel_subscribers[normalized].add(connection_id)
                subscribed.append(normalized)

        logger.info(
            "realtime_subscribed connection=%s channels=%s",
            connection_id,
            subscribed,
        )
        return subscribed

    async def unsubscribe(self, connection_id: str, channels: list[str]) -> list[str]:
        if not channels:
            raise SubscriptionError("channels list is required")

        connection = await connection_manager.get(connection_id)
        removed: list[str] = []
        async with self._lock:
            for channel in channels:
                normalized = ChannelManager.validate_channel(channel)
                if normalized in connection.subscribed_channels:
                    connection.subscribed_channels.discard(normalized)
                    bucket = self._channel_subscribers.get(normalized)
                    if bucket is not None:
                        bucket.discard(connection_id)
                        if not bucket:
                            del self._channel_subscribers[normalized]
                    removed.append(normalized)

        logger.info(
            "realtime_unsubscribed connection=%s channels=%s",
            connection_id,
            removed,
        )
        return removed

    async def subscribers(self, channel: str) -> set[str]:
        normalized = ChannelManager.validate_channel(channel)
        async with self._lock:
            return set(self._channel_subscribers.get(normalized, ()))

    async def subscriptions_snapshot(self) -> dict[str, list[str]]:
        async with self._lock:
            return {
                channel: sorted(connection_ids)
                for channel, connection_ids in self._channel_subscribers.items()
            }

    async def remove_connection(self, connection_id: str) -> None:
        async with self._lock:
            for channel, connection_ids in list(self._channel_subscribers.items()):
                connection_ids.discard(connection_id)
                if not connection_ids:
                    del self._channel_subscribers[channel]

        try:
            connection = await connection_manager.get(connection_id)
        except ConnectionNotFoundError:
            return
        connection.subscribed_channels.clear()

    def reset(self) -> None:
        self._channel_subscribers.clear()


subscription_manager = SubscriptionManager()
