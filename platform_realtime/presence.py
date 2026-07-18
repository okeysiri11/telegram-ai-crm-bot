# Online presence — users and channel occupancy.

from __future__ import annotations

import asyncio
from collections import Counter

from platform_realtime.connection_manager import connection_manager


class PresenceTracker:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def snapshot(self) -> dict[str, object]:
        connections = await connection_manager.list_connections()
        users = {conn.user_telegram_id for conn in connections}
        channel_counts: Counter[str] = Counter()
        role_counts: Counter[str] = Counter()
        for conn in connections:
            role_counts[conn.role] += 1
            for channel in conn.subscribed_channels:
                channel_counts[channel] += 1

        return {
            "online_users": sorted(users),
            "online_user_count": len(users),
            "connection_count": len(connections),
            "roles": dict(role_counts),
            "channel_presence": dict(channel_counts),
        }

    async def is_user_online(self, user_telegram_id: int) -> bool:
        conns = await connection_manager.connections_for_user(user_telegram_id)
        return len(conns) > 0


presence_tracker = PresenceTracker()
